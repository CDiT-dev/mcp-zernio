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

# ---------------------------------------------------------------------------
# Auth: pending tokens (10 min) and active sessions (24h)
# ---------------------------------------------------------------------------

_inbox_tokens: dict[str, float] = {}
_inbox_sessions: dict[str, float] = {}

_TOKEN_TTL = 600  # 10 minutes
_SESSION_TTL = 86400  # 24 hours


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
        max_age=86400,
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
    participant = item.get("participant") or item.get("contact") or {}
    name = participant.get("name") or participant.get("displayName") or "Unknown"
    username = participant.get("username") or participant.get("handle") or ""
    last_message = item.get("lastMessage") or item.get("preview") or ""
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
        "timestamp": item.get("updatedAt") or item.get("createdAt") or "",
        "unread": item.get("unread", False),
        "hidden": item.get("hidden", False),
        "accountId": item.get("accountId", ""),
        "platformData": {
            k: v
            for k, v in item.items()
            if k
            not in {
                "id",
                "platform",
                "participant",
                "contact",
                "lastMessage",
                "preview",
                "updatedAt",
                "createdAt",
                "unread",
                "hidden",
                "accountId",
            }
        },
    }


def _normalize_comment(item: dict[str, Any]) -> dict[str, Any]:
    """Normalize a comment item to the unified stream shape."""
    author = item.get("author") or item.get("user") or {}
    name = author.get("name") or author.get("displayName") or "Unknown"
    username = author.get("username") or author.get("handle") or ""
    text = item.get("text") or item.get("message") or item.get("body") or ""
    return {
        "id": item.get("id", ""),
        "type": "comment",
        "platform": item.get("platform", ""),
        "participant": {
            "name": name,
            "username": username,
            "initials": _make_initials(name),
        },
        "preview": str(text)[:100],
        "timestamp": item.get("createdAt") or item.get("updatedAt") or "",
        "unread": item.get("unread", False),
        "hidden": item.get("hidden", False),
        "accountId": item.get("accountId", ""),
        "platformData": {
            "postId": item.get("postId", ""),
            "commentId": item.get("commentId") or item.get("id", ""),
            **{
                k: v
                for k, v in item.items()
                if k
                not in {
                    "id",
                    "platform",
                    "author",
                    "user",
                    "text",
                    "message",
                    "body",
                    "createdAt",
                    "updatedAt",
                    "unread",
                    "hidden",
                    "accountId",
                    "postId",
                    "commentId",
                }
            },
        },
    }


def _normalize_review(item: dict[str, Any]) -> dict[str, Any]:
    """Normalize a review item to the unified stream shape."""
    reviewer = item.get("reviewer") or item.get("author") or {}
    name = reviewer.get("name") or reviewer.get("displayName") or "Unknown"
    username = reviewer.get("username") or reviewer.get("handle") or ""
    text = item.get("text") or item.get("body") or item.get("comment") or ""
    return {
        "id": item.get("id", ""),
        "type": "review",
        "platform": item.get("platform", ""),
        "participant": {
            "name": name,
            "username": username,
            "initials": _make_initials(name),
        },
        "preview": str(text)[:100],
        "timestamp": item.get("createdAt") or item.get("updatedAt") or "",
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
from zernio_mcp.inbox_html import INBOX_HTML as _INBOX_HTML


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
            return HTMLResponse(
                "<h1>Invalid or expired inbox link</h1>"
                "<p>Please request a new inbox link from Claude.</p>",
                status_code=403,
            )
        # Consume the token and create a session
        _inbox_tokens.pop(token, None)
        sid = secrets.token_urlsafe(32)
        _inbox_sessions[sid] = time.monotonic()
        response = HTMLResponse(_INBOX_HTML)
        _set_session_cookie(response, sid)
        return response

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

    @mcp.custom_route("/inbox/api/conversations/{conv_id}", methods=["GET"])
    async def inbox_conversation(request: Request) -> JSONResponse:
        if not _validate_session(request):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        conv_id = request.path_params["conv_id"]
        client = ZernioClient(http_client=get_shared_client())

        try:
            conversation, messages = await asyncio.gather(
                client.get(f"/v1/inbox/conversations/{conv_id}"),
                client.get(f"/v1/inbox/conversations/{conv_id}/messages"),
            )

            sid = _get_session_id(request)
            response = JSONResponse(
                {
                    "conversation": conversation,
                    "messages": (
                        messages
                        if isinstance(messages, list)
                        else messages.get("data")
                        or messages.get("messages")
                        or []
                    ),
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
