"""Universal social media inbox UI backend.

Provides a browser-based unified inbox at /inbox so users can view and respond
to DMs, comments, and reviews across all connected social platforms.

Flow:
  1. Claude calls inbox_get_link() -> returns URL to /inbox page with token
  2. User opens the link, token is exchanged for a session cookie
  3. SPA makes API calls to /inbox/api/* endpoints
  4. Server proxies requests to Zernio API, normalizes responses
"""

from __future__ import annotations

import asyncio
import secrets
import time
from typing import Any

from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response

from zernio_mcp.client import ZernioAPIError, ZernioClient, get_shared_client
from zernio_mcp.config import settings

# ---------------------------------------------------------------------------
# Auth: pending tokens (10 min) and active sessions (24h)
# ---------------------------------------------------------------------------

_inbox_tokens: dict[str, float] = {}
_inbox_sessions: dict[str, float] = {}

_TOKEN_TTL = 600  # 10 minutes
_SESSION_TTL = 2592000  # 30 days


def _cleanup_expired() -> None:
    """Remove expired tokens and sessions."""
    now = time.monotonic()
    for token, ts in list(_inbox_tokens.items()):
        if (now - ts) > _TOKEN_TTL:
            del _inbox_tokens[token]
    for sid, ts in list(_inbox_sessions.items()):
        if (now - ts) > _SESSION_TTL:
            del _inbox_sessions[sid]


def create_inbox_token() -> str:
    """Create a short-lived token that authorizes inbox access."""
    _cleanup_expired()
    token = secrets.token_urlsafe(32)
    _inbox_tokens[token] = time.monotonic()
    return token


def _validate_session(request: Request) -> bool:
    """Check inbox_session cookie against active sessions."""
    _cleanup_expired()
    sid = request.cookies.get("inbox_session")
    if not sid or sid not in _inbox_sessions:
        return False
    # Refresh TTL on access
    _inbox_sessions[sid] = time.monotonic()
    return True


def _set_session_cookie(response: JSONResponse | HTMLResponse, sid: str) -> None:
    """Set the inbox_session cookie on a response."""
    response.set_cookie(
        "inbox_session",
        sid,
        httponly=True,
        max_age=2592000,
        samesite="lax",
    )


def _get_session_id(request: Request) -> str | None:
    """Get the current session id from cookie."""
    return request.cookies.get("inbox_session")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_initials(name: str) -> str:
    """Generate initials from a participant name (first letter of first two words)."""
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    if parts:
        return parts[0][0].upper()
    return "?"


def _normalize_conversation(item: dict[str, Any]) -> dict[str, Any]:
    """Normalize a conversation (DM) item to the unified stream shape."""
    # Zernio uses different field names depending on platform
    participant = item.get("participant") or item.get("contact") or {}
    name = (
        participant.get("name")
        or participant.get("displayName")
        or item.get("participantName")
        or item.get("senderName")
        or "Unknown"
    )
    username = (
        participant.get("username")
        or participant.get("handle")
        or item.get("participantUsername")
        or item.get("accountUsername")
        or ""
    )
    last_message = item.get("lastMessage") or item.get("preview") or item.get("snippet") or ""
    timestamp = (
        item.get("updatedAt")
        or item.get("createdAt")
        or item.get("updatedTime")
        or item.get("lastMessageAt")
        or ""
    )
    _excluded = {
        "id", "platform", "participant", "contact", "lastMessage", "preview",
        "snippet", "updatedAt", "createdAt", "updatedTime", "lastMessageAt",
        "unread", "hidden", "accountId", "participantName", "senderName",
        "participantUsername", "accountUsername",
    }
    return {
        "id": item.get("id", ""),
        "type": "dm",
        "platform": item.get("platform", ""),
        "participant": {
            "name": name,
            "username": username,
            "initials": _make_initials(name),
        },
        "preview": str(last_message)[:100],
        "timestamp": timestamp,
        "unread": item.get("unread", False),
        "hidden": item.get("hidden", False),
        "accountId": item.get("accountId", ""),
        "platformData": {k: v for k, v in item.items() if k not in _excluded},
    }


def _normalize_comment(item: dict[str, Any]) -> dict[str, Any]:
    """Normalize a comment item to the unified stream shape."""
    # Zernio returns comment/post data with various field names
    author = item.get("author") or item.get("user") or {}
    name = (
        author.get("name")
        or author.get("displayName")
        or item.get("authorName")
        or item.get("accountUsername")
        or item.get("senderName")
        or "Unknown"
    )
    username = (
        author.get("username")
        or author.get("handle")
        or item.get("authorUsername")
        or item.get("accountUsername")
        or ""
    )
    text = (
        item.get("text")
        or item.get("message")
        or item.get("body")
        or item.get("content")
        or ""
    )
    timestamp = (
        item.get("createdAt")
        or item.get("updatedAt")
        or item.get("createdTime")
        or item.get("updatedTime")
        or ""
    )
    comment_count = item.get("commentCount", 0)
    preview = str(text)[:100]
    if comment_count:
        preview = f"[{comment_count} comment{'s' if comment_count != 1 else ''}] {preview}"

    _excluded = {
        "id", "platform", "author", "user", "text", "message", "body",
        "content", "createdAt", "updatedAt", "createdTime", "updatedTime",
        "unread", "hidden", "accountId", "postId", "commentId",
        "authorName", "authorUsername", "accountUsername", "senderName",
        "commentCount",
    }
    return {
        "id": item.get("id", ""),
        "type": "comment",
        "platform": item.get("platform", ""),
        "participant": {
            "name": name,
            "username": username,
            "initials": _make_initials(name),
        },
        "preview": preview,
        "timestamp": timestamp,
        "unread": item.get("unread", False),
        "hidden": item.get("hidden", False),
        "accountId": item.get("accountId", ""),
        "platformData": {
            "postId": item.get("postId") or item.get("id", ""),
            "commentId": item.get("commentId") or item.get("id", ""),
            "permalink": item.get("permalink", ""),
            "commentCount": comment_count,
            "likeCount": item.get("likeCount", 0),
            **{k: v for k, v in item.items() if k not in _excluded},
        },
    }


def _normalize_review(item: dict[str, Any]) -> dict[str, Any]:
    """Normalize a review item to the unified stream shape."""
    reviewer = item.get("reviewer") or item.get("author") or {}
    name = (
        reviewer.get("name")
        or reviewer.get("displayName")
        or item.get("reviewerName")
        or item.get("authorName")
        or "Unknown"
    )
    username = (
        reviewer.get("username")
        or reviewer.get("handle")
        or item.get("reviewerUsername")
        or ""
    )
    text = (
        item.get("text")
        or item.get("body")
        or item.get("comment")
        or item.get("content")
        or ""
    )
    timestamp = (
        item.get("createdAt")
        or item.get("updatedAt")
        or item.get("createdTime")
        or item.get("updatedTime")
        or ""
    )
    rating = item.get("rating") or item.get("starRating") or 0
    return {
        "id": item.get("id", ""),
        "type": "review",
        "platform": item.get("platform", "google"),
        "participant": {
            "name": name,
            "username": username,
            "initials": _make_initials(name),
        },
        "preview": ("★" * rating + " " if rating else "") + str(text)[:100],
        "timestamp": timestamp,
        "unread": item.get("unread", False),
        "hidden": item.get("hidden", False),
        "accountId": item.get("accountId", ""),
        "platformData": {
            "reviewId": item.get("reviewId") or item.get("id", ""),
            "rating": item.get("rating"),
            **{
                k: v
                for k, v in item.items()
                if k
                not in {
                    "id",
                    "platform",
                    "reviewer",
                    "author",
                    "text",
                    "body",
                    "comment",
                    "createdAt",
                    "updatedAt",
                    "unread",
                    "hidden",
                    "accountId",
                    "reviewId",
                    "rating",
                }
            },
        },
    }


# ---------------------------------------------------------------------------
# Placeholder HTML
# ---------------------------------------------------------------------------

# HTML/CSS/JS loaded from separate modules
from zernio_mcp.inbox_html import INBOX_HTML as _INBOX_HTML_RAW, INBOX_LOGIN_HTML as _INBOX_LOGIN_HTML

# Cache-bust JS URL with startup timestamp so deploys always serve fresh JS
_INBOX_HTML = _INBOX_HTML_RAW.replace("__CACHE_BUST__", str(int(time.time())))


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------


def register_inbox_routes(mcp) -> None:  # noqa: C901
    """Register /inbox routes on the FastMCP server."""

    # -- GET /inbox — exchange token for session, serve HTML ----------------

    @mcp.custom_route("/inbox", methods=["GET"])
    async def inbox_page(request: Request) -> HTMLResponse:
        token = request.query_params.get("token", "")
        if not token or token not in _inbox_tokens:
            # If they already have a valid session, let them through
            if _validate_session(request):
                return HTMLResponse(_INBOX_HTML)
            # Show login page
            has_magic = bool(settings.resend_api_key and settings.inbox_email)
            masked_email = ""
            if has_magic and settings.inbox_email:
                parts = settings.inbox_email.split("@")
                masked_email = parts[0][:2] + "***@" + parts[1] if len(parts) == 2 else ""
            login_html = _INBOX_LOGIN_HTML.replace(
                "__MAGIC_ENABLED__", "true" if has_magic else "false"
            ).replace(
                "__MASKED_EMAIL__", masked_email
            )
            return HTMLResponse(login_html)
        # Consume the token and create a session
        _inbox_tokens.pop(token, None)
        sid = secrets.token_urlsafe(32)
        _inbox_sessions[sid] = time.monotonic()
        response = HTMLResponse(_INBOX_HTML)
        _set_session_cookie(response, sid)
        return response

    # -- GET /inbox/conv/{id}, /inbox/archived, /inbox/sent — SPA sub-routes --

    @mcp.custom_route("/inbox/conv/{conv_id:path}", methods=["GET"])
    async def inbox_conv_page(request: Request) -> HTMLResponse:
        if _validate_session(request):
            return HTMLResponse(_INBOX_HTML)
        return HTMLResponse(
            '<meta http-equiv="refresh" content="0;url=/inbox">',
            status_code=302,
        )

    @mcp.custom_route("/inbox/archived", methods=["GET"])
    async def inbox_archived_page(request: Request) -> HTMLResponse:
        if _validate_session(request):
            return HTMLResponse(_INBOX_HTML)
        return HTMLResponse(
            '<meta http-equiv="refresh" content="0;url=/inbox">',
            status_code=302,
        )

    @mcp.custom_route("/inbox/sent", methods=["GET"])
    async def inbox_sent_page(request: Request) -> HTMLResponse:
        if _validate_session(request):
            return HTMLResponse(_INBOX_HTML)
        return HTMLResponse(
            '<meta http-equiv="refresh" content="0;url=/inbox">',
            status_code=302,
        )

    # -- POST /inbox/auth — passphrase login ---------------------------------

    @mcp.custom_route("/inbox/auth", methods=["POST"])
    async def inbox_auth(request: Request) -> JSONResponse:
        if not settings.inbox_passphrase:
            return JSONResponse({"error": "Login not configured"}, status_code=503)

        body = await request.json()
        passphrase = body.get("passphrase", "")

        if not secrets.compare_digest(passphrase, settings.inbox_passphrase):
            return JSONResponse({"error": "Invalid passphrase"}, status_code=401)

        sid = secrets.token_urlsafe(32)
        _inbox_sessions[sid] = time.monotonic()
        response = JSONResponse({"success": True})
        _set_session_cookie(response, sid)
        return response

    # -- POST /inbox/auth/magic — send magic link via Resend ----------------

    @mcp.custom_route("/inbox/auth/magic", methods=["POST"])
    async def inbox_auth_magic(request: Request) -> JSONResponse:
        if not settings.resend_api_key or not settings.inbox_email:
            return JSONResponse({"error": "Magic links not configured"}, status_code=503)

        token = create_inbox_token()
        link = f"{settings.public_url.rstrip('/')}/inbox?token={token}"

        try:
            import resend
            resend.api_key = settings.resend_api_key
            resend.Emails.send({
                "from": "Zernio Inbox <inbox@cdit-dev.de>",
                "to": settings.inbox_email,
                "subject": "Your Zernio Inbox link",
                "html": (
                    '<div style="font-family:sans-serif;max-width:420px;margin:40px auto;text-align:center">'
                    '<h2 style="margin-bottom:8px">Zernio Inbox</h2>'
                    '<p style="color:#666;margin-bottom:24px">Click below to open your inbox. This link expires in 10 minutes.</p>'
                    f'<a href="{link}" style="display:inline-block;padding:12px 32px;background:#2a9d4e;color:white;'
                    'text-decoration:none;font-weight:600;border:2px solid #000;box-shadow:4px 4px 0px 0px #000">'
                    'Open Inbox</a>'
                    '<p style="color:#999;font-size:12px;margin-top:24px">If you didn\'t request this, you can safely ignore it.</p>'
                    '</div>'
                ),
            })
        except Exception as e:
            return JSONResponse({"error": f"Failed to send email: {type(e).__name__}"}, status_code=500)

        parts = settings.inbox_email.split("@")
        masked = parts[0][:2] + "***@" + parts[1] if len(parts) == 2 else "your email"
        return JSONResponse({"success": True, "message": f"Magic link sent to {masked}"})

    # -- GET /inbox/app.js — serve the SPA JavaScript ----------------------

    @mcp.custom_route("/inbox/app.js", methods=["GET"])
    async def inbox_js(request: Request) -> Response:
        from zernio_mcp.inbox_app_core import INBOX_JS_CORE
        from zernio_mcp.inbox_app_interactions import INBOX_JS_INTERACTIONS
        js = INBOX_JS_CORE + "\n" + INBOX_JS_INTERACTIONS
        return Response(
            content=js,
            media_type="application/javascript",
            headers={"Cache-Control": "no-cache"},
        )

    # -- GET /inbox/api/stream — unified inbox stream ----------------------

    @mcp.custom_route("/inbox/api/stream", methods=["GET"])
    async def inbox_stream(request: Request) -> JSONResponse:
        if not _validate_session(request):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        # Query params for filtering
        item_type = request.query_params.get("type")  # dm, comment, review
        platform = request.query_params.get("platform")
        status = request.query_params.get("status")
        limit = int(request.query_params.get("limit", "50"))
        offset = int(request.query_params.get("offset", "0"))

        client = ZernioClient(http_client=get_shared_client())

        # Build query params for upstream calls
        upstream_params: dict[str, Any] = {}
        if platform:
            upstream_params["platform"] = platform
        if status:
            upstream_params["status"] = status

        try:
            # Fetch all three streams concurrently
            tasks = []
            fetch_types = []

            if not item_type or item_type == "dm":
                tasks.append(client.get("/v1/inbox/conversations", **upstream_params))
                fetch_types.append("dm")
            if not item_type or item_type == "comment":
                tasks.append(client.get("/v1/inbox/comments", **upstream_params))
                fetch_types.append("comment")
            if not item_type or item_type == "review":
                tasks.append(client.get("/v1/inbox/reviews", **upstream_params))
                fetch_types.append("review")

            results = await asyncio.gather(*tasks, return_exceptions=True)

            all_items: list[dict[str, Any]] = []
            unread_counts = {"dm": 0, "comment": 0, "review": 0}

            for fetch_type, result in zip(fetch_types, results):
                if isinstance(result, Exception):
                    continue  # skip failed streams, return what we can

                # Extract items list from response (handle both list and dict)
                raw_items = (
                    result
                    if isinstance(result, list)
                    else result.get("data")
                    or result.get("items")
                    or result.get("conversations")
                    or result.get("comments")
                    or result.get("reviews")
                    or []
                )

                for raw in raw_items:
                    if fetch_type == "dm":
                        normalized = _normalize_conversation(raw)
                    elif fetch_type == "comment":
                        normalized = _normalize_comment(raw)
                    else:
                        normalized = _normalize_review(raw)
                    all_items.append(normalized)
                    if normalized.get("unread"):
                        unread_counts[fetch_type] += 1

            # Sort by timestamp descending
            all_items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            total = len(all_items)
            paged = all_items[offset : offset + limit]

            # Refresh session cookie
            sid = _get_session_id(request)
            response = JSONResponse(
                {
                    "items": paged,
                    "total": total,
                    "unreadCounts": unread_counts,
                    "lastUpdated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
            )
            if sid:
                _set_session_cookie(response, sid)
            return response

        except ZernioAPIError as e:
            return JSONResponse(
                {"error": str(e)},
                status_code=e.status_code or 502,
            )

    # -- GET /inbox/api/conversations/{conv_id} — single conversation ------

    @mcp.custom_route("/inbox/api/conversations/{conv_id:path}", methods=["GET"])
    async def inbox_conversation(request: Request) -> JSONResponse:
        if not _validate_session(request):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        conv_id = request.path_params["conv_id"]
        account_id = request.query_params.get("accountId", "")
        item_type = request.query_params.get("type", "dm")
        client = ZernioClient(http_client=get_shared_client())

        try:
            params: dict[str, Any] = {}
            if account_id:
                params["accountId"] = account_id

            if item_type == "comment":
                # For comments: fetch the post's comment thread
                comments_data = await client.get(
                    f"/v1/inbox/comments/{conv_id}", **params
                )
                raw_comments = (
                    comments_data
                    if isinstance(comments_data, list)
                    else comments_data.get("data")
                    or comments_data.get("comments")
                    or []
                )

                # Build conversation from the post info
                normalized_conv = {
                    "id": conv_id,
                    "type": "comment",
                    "platform": raw_comments[0].get("platform", "") if raw_comments else "",
                    "participant": {
                        "name": "Post Comments",
                        "username": params.get("accountId", ""),
                        "initials": "PC",
                    },
                    "accountId": account_id,
                    "platformUrl": "",
                    "platformData": {"postId": conv_id},
                    "replyAs": {"username": ""},
                    "status": "",
                }

                # Each comment becomes a message
                normalized_msgs = []
                for c in raw_comments:
                    author_name = (
                        c.get("authorName")
                        or c.get("username")
                        or c.get("from", {}).get("name", "")
                        or c.get("from", {}).get("username", "")
                        or "Unknown"
                    )
                    author_username = (
                        c.get("authorUsername")
                        or c.get("username")
                        or c.get("from", {}).get("username", "")
                        or ""
                    )
                    text = (
                        c.get("text")
                        or c.get("message")
                        or c.get("content")
                        or c.get("body")
                        or ""
                    )
                    timestamp = (
                        c.get("createdAt")
                        or c.get("timestamp")
                        or c.get("createdTime")
                        or ""
                    )
                    is_own = c.get("isOwn", False) or c.get("direction") == "outgoing"
                    like_count = c.get("likeCount", 0)
                    normalized_msgs.append({
                        "id": c.get("id", ""),
                        "content": text,
                        "sender": "me" if is_own else "them",
                        "senderName": author_name,
                        "senderUsername": author_username,
                        "timestamp": timestamp,
                        "status": "sent",
                        "likeCount": like_count,
                        "attachments": c.get("attachments") or [],
                    })

                    # Update conv info from first comment's platform data
                    if not normalized_conv["platformUrl"]:
                        normalized_conv["platformUrl"] = c.get("permalink", "")
                    if not normalized_conv["platform"]:
                        normalized_conv["platform"] = c.get("platform", "")
                    if not normalized_conv["replyAs"]["username"]:
                        normalized_conv["replyAs"]["username"] = c.get("accountUsername", "")

            else:
                # For DMs: fetch conversation + messages
                conversation, messages = await asyncio.gather(
                    client.get(f"/v1/inbox/conversations/{conv_id}", **params),
                    client.get(f"/v1/inbox/conversations/{conv_id}/messages", **params),
                )

                conv_data = conversation.get("data") or conversation
                conv_name = (
                    conv_data.get("participantName")
                    or conv_data.get("senderName")
                    or "Unknown"
                )
                conv_username = (
                    conv_data.get("participantUsername")
                    or conv_data.get("accountUsername")
                    or ""
                )
                conv_platform = conv_data.get("platform", "")
                conv_url = (
                    conv_data.get("url")
                    or conv_data.get("platformUrl")
                    or conv_data.get("permalink")
                    or conv_data.get("instagramProfile", {}).get("url", "")
                    or ""
                )
                normalized_conv = {
                    "id": conv_data.get("id", conv_id),
                    "type": "dm",
                    "platform": conv_platform,
                    "participant": {
                        "name": conv_name,
                        "username": conv_username,
                        "initials": _make_initials(conv_name),
                    },
                    "accountId": conv_data.get("accountId", account_id),
                    "platformUrl": conv_url,
                    "replyAs": {"username": conv_data.get("accountUsername", "")},
                    "status": conv_data.get("status", ""),
                }

                raw_msgs = (
                    messages
                    if isinstance(messages, list)
                    else messages.get("data")
                    or messages.get("messages")
                    or []
                )
                normalized_msgs = []
                for msg in raw_msgs:
                    direction = msg.get("direction", "")
                    sender = "me" if direction == "outgoing" else "them"
                    normalized_msgs.append({
                        "id": msg.get("id", ""),
                        "content": msg.get("message") or msg.get("text") or msg.get("content") or "",
                        "sender": sender,
                        "timestamp": msg.get("createdAt") or msg.get("timestamp") or "",
                        "status": "sent",
                        "attachments": msg.get("attachments") or [],
                    })

            sid = _get_session_id(request)
            response = JSONResponse({
                "conversation": normalized_conv,
                "messages": normalized_msgs,
            })
            if sid:
                _set_session_cookie(response, sid)
            return response

        except ZernioAPIError as e:
            return JSONResponse(
                {"error": str(e)},
                status_code=e.status_code or 502,
            )

    # -- POST /inbox/api/reply — send a reply ------------------------------

    @mcp.custom_route("/inbox/api/reply", methods=["POST"])
    async def inbox_reply(request: Request) -> JSONResponse:
        if not _validate_session(request):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

        item_id = body.get("itemId", "")
        item_type = body.get("itemType", "")
        content = body.get("content", "")
        private = body.get("private", False)
        platform_data = body.get("platformData") or {}

        if not item_id or not item_type or not content:
            return JSONResponse(
                {"error": "itemId, itemType, and content are required"},
                status_code=400,
            )

        client = ZernioClient(http_client=get_shared_client())

        try:
            if item_type == "dm":
                conversation_id = platform_data.get("conversationId") or item_id
                result = await client.post(
                    f"/v1/inbox/conversations/{conversation_id}/messages",
                    {"content": content},
                )
            elif item_type == "comment" and not private:
                post_id = platform_data.get("postId", "")
                if not post_id:
                    return JSONResponse(
                        {"error": "platformData.postId is required for comment replies"},
                        status_code=400,
                    )
                result = await client.post(
                    f"/v1/inbox/comments/{post_id}",
                    {"content": content},
                )
            elif item_type == "comment" and private:
                post_id = platform_data.get("postId", "")
                comment_id = platform_data.get("commentId") or item_id
                if not post_id:
                    return JSONResponse(
                        {"error": "platformData.postId is required for private replies"},
                        status_code=400,
                    )
                result = await client.post(
                    f"/v1/inbox/comments/{post_id}/{comment_id}/private-reply",
                    {"content": content},
                )
            elif item_type == "review":
                review_id = platform_data.get("reviewId") or item_id
                result = await client.post(
                    f"/v1/inbox/reviews/{review_id}/reply",
                    {"content": content},
                )
            else:
                return JSONResponse(
                    {"error": f"Unknown itemType: {item_type}"},
                    status_code=400,
                )

            sid = _get_session_id(request)
            response = JSONResponse({"ok": True, "data": result})
            if sid:
                _set_session_cookie(response, sid)
            return response

        except ZernioAPIError as e:
            return JSONResponse(
                {"error": str(e)},
                status_code=e.status_code or 502,
            )

    # -- POST /inbox/api/action — perform an action on an item -------------

    @mcp.custom_route("/inbox/api/action", methods=["POST"])
    async def inbox_action(request: Request) -> JSONResponse:
        if not _validate_session(request):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

        action = body.get("action", "")
        item_id = body.get("itemId", "")
        item_type = body.get("itemType", "")
        platform_data = body.get("platformData") or {}

        if not action or not item_id:
            return JSONResponse(
                {"error": "action and itemId are required"},
                status_code=400,
            )

        client = ZernioClient(http_client=get_shared_client())

        try:
            result: dict[str, Any] = {}

            if action == "archive":
                result = await client.put(
                    f"/v1/inbox/conversations/{item_id}",
                    {"status": "archived"},
                )
            elif action == "read":
                result = await client.put(
                    f"/v1/inbox/conversations/{item_id}",
                    {"status": "read"},
                )
            elif action == "hide":
                post_id = platform_data.get("postId", "")
                comment_id = platform_data.get("commentId") or item_id
                if not post_id:
                    return JSONResponse(
                        {"error": "platformData.postId is required for hide"},
                        status_code=400,
                    )
                result = await client.post(
                    f"/v1/inbox/comments/{post_id}/{comment_id}/hide",
                    {},
                )
            elif action == "delete" and item_type == "comment":
                post_id = platform_data.get("postId", "")
                comment_id = platform_data.get("commentId") or item_id
                if not post_id:
                    return JSONResponse(
                        {"error": "platformData.postId is required for delete"},
                        status_code=400,
                    )
                result = await client.delete(
                    f"/v1/inbox/comments/{post_id}",
                    commentId=comment_id,
                )
            elif action == "delete" and item_type == "dm":
                conv_id = platform_data.get("conversationId") or platform_data.get("convId", "")
                msg_id = platform_data.get("messageId") or platform_data.get("msgId") or item_id
                if not conv_id:
                    return JSONResponse(
                        {"error": "platformData.conversationId is required for message delete"},
                        status_code=400,
                    )
                result = await client.delete(
                    f"/v1/inbox/conversations/{conv_id}/messages/{msg_id}",
                )
            elif action == "like":
                post_id = platform_data.get("postId", "")
                comment_id = platform_data.get("commentId") or item_id
                if not post_id:
                    return JSONResponse(
                        {"error": "platformData.postId is required for like"},
                        status_code=400,
                    )
                result = await client.post(
                    f"/v1/inbox/comments/{post_id}/{comment_id}/like",
                    {},
                )
            elif action == "follow":
                account_id = platform_data.get("accountId") or item_id
                result = await client.post(
                    "/v1/twitter/follow",
                    {"accountId": account_id},
                )
            else:
                return JSONResponse(
                    {"error": f"Unknown action: {action}"},
                    status_code=400,
                )

            sid = _get_session_id(request)
            response = JSONResponse({"ok": True, "data": result})
            if sid:
                _set_session_cookie(response, sid)
            return response

        except ZernioAPIError as e:
            return JSONResponse(
                {"error": str(e)},
                status_code=e.status_code or 502,
            )

    # -- PATCH /inbox/api/messages/{message_id} — edit a message -----------

    @mcp.custom_route("/inbox/api/messages/{message_id}", methods=["PATCH"])
    async def inbox_edit_message(request: Request) -> JSONResponse:
        if not _validate_session(request):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        message_id = request.path_params["message_id"]

        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

        conversation_id = body.get("conversationId", "")
        content = body.get("content", "")

        if not conversation_id or not content:
            return JSONResponse(
                {"error": "conversationId and content are required"},
                status_code=400,
            )

        client = ZernioClient(http_client=get_shared_client())

        try:
            result = await client.patch(
                f"/v1/inbox/conversations/{conversation_id}/messages/{message_id}",
                {"content": content},
            )

            sid = _get_session_id(request)
            response = JSONResponse({"ok": True, "data": result})
            if sid:
                _set_session_cookie(response, sid)
            return response

        except ZernioAPIError as e:
            return JSONResponse(
                {"error": str(e)},
                status_code=e.status_code or 502,
            )
