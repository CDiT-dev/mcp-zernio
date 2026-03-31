"""MCP server with 13 Zernio social media management tools."""

from __future__ import annotations

import base64
import os
from typing import Literal

from fastmcp import FastMCP
from mcp.types import ToolAnnotations

from zernio_mcp.auth import build_auth
from zernio_mcp.client import (
    ZernioAPIError,
    ZernioClient,
    SSRFError,
    strip_pii,
    ALLOWED_MEDIA_TYPES,
)
from zernio_mcp.config import settings

mcp = FastMCP("mcp-zernio", auth=build_auth())

MAX_BASE64_BYTES = 2 * 1024 * 1024  # 2 MB


def _client() -> ZernioClient:
    return ZernioClient()


def _error(msg: str) -> dict:
    return {"error": msg}


# ---------------------------------------------------------------------------
# 1. Social Accounts (3 tools)
# ---------------------------------------------------------------------------


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def accounts_list() -> dict:
    """List all connected social media accounts.

    Returns each account's id, platform, username, displayName, and profileName.
    Use this to find account IDs before calling posts_create.
    """
    try:
        data = await _client().get("/v1/accounts")
        accounts = data.get("accounts", data if isinstance(data, list) else [])
        return {"accounts": [strip_pii(a) for a in accounts]}
    except ZernioAPIError as e:
        return _error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def accounts_health() -> dict:
    """Check token health and expiry status for all connected accounts.

    Returns status per account: "healthy" or "expired".
    When a token is expired, includes reauth instructions directing the user
    to app.zernio.com/accounts to reconnect.
    """
    try:
        data = await _client().get("/v1/accounts/health")
        accounts = data.get("accounts", data if isinstance(data, list) else [])
        results = []
        for a in accounts:
            entry = strip_pii(a)
            if entry.get("status") in ("expired", "revoked", "error"):
                entry["reauth_instructions"] = (
                    "Your connection needs to be renewed. "
                    "Go to https://app.zernio.com/accounts to reconnect this account."
                )
            results.append(entry)
        return {"accounts": results}
    except ZernioAPIError as e:
        return _error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def profiles_list() -> dict:
    """List all brand profile groupings with their associated account IDs.

    A profile is a brand grouping containing one or more connected accounts.
    Use profiles_list to identify which accounts belong to a brand, then pass
    account_ids from the profile to posts_create.
    """
    try:
        return await _client().get("/v1/profiles")
    except ZernioAPIError as e:
        return _error(e.message)


# ---------------------------------------------------------------------------
# 2. Post Management (6 tools)
# ---------------------------------------------------------------------------


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
async def posts_create(
    content: str,
    platforms: list[dict],
    publish_now: bool = False,
    scheduled_for: str | None = None,
    media_urls: list[str] | None = None,
    profile_id: str | None = None,
) -> dict:
    """Create a social media post (draft, scheduled, or immediate publish).

    Three modes:
      - Draft (default): omit publish_now and scheduled_for
      - Immediate: publish_now=True
      - Scheduled: scheduled_for="2026-04-01T09:00:00Z" (ISO 8601)

    Get account IDs first via accounts_list. Each entry in platforms requires:
      {"platform": "twitter", "accountId": "acc_123"}

    For cross-posting, include multiple entries in the platforms array.
    When cross-posting, verify each platform's status in the response —
    partial failures are possible (e.g., Twitter succeeds but Instagram fails).

    If the user has multiple accounts for the target platform and hasn't
    specified which one, call profiles_list first to identify the correct
    brand context, then confirm before posting.

    Args:
        content: Post text content.
        platforms: List of {"platform": str, "accountId": str} targets.
        publish_now: If True, publish immediately. Default: False (draft).
        scheduled_for: ISO 8601 datetime for scheduling. Overrides publish_now.
        media_urls: List of publicUrl strings from media_upload.
        profile_id: Optional profile ID for account disambiguation.
    """
    try:
        body: dict = {
            "content": content,
            "platforms": platforms,
        }
        if scheduled_for:
            body["scheduledFor"] = scheduled_for
        elif publish_now:
            body["publishNow"] = True
        if media_urls:
            body["mediaItems"] = [{"url": u, "type": "image"} for u in media_urls]
        if profile_id:
            body["profileId"] = profile_id

        return await _client().post("/v1/posts", body)
    except ZernioAPIError as e:
        return _error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def posts_get(post_id: str) -> dict:
    """Get a single post by ID, including status, platformPostUrl, and failure_reason.

    Use this to check post status after creation, especially for async publish
    operations. For failed posts, the response includes failure_reason explaining
    why it failed (e.g., "Image aspect ratio rejected", "Caption exceeds limit").
    """
    try:
        return await _client().get(f"/v1/posts/{post_id}")
    except ZernioAPIError as e:
        return _error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def posts_list(
    status: str | None = None,
    platform: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """List posts with optional filters.

    Filter by status (draft, scheduled, published, failed), platform, or
    date range (ISO 8601, e.g. "2026-04-01T00:00:00Z").

    To see failed posts: posts_list(status="failed")
    To see tomorrow's schedule: posts_list(status="scheduled", from_date=..., to_date=...)

    Args:
        status: Filter by post status.
        platform: Filter by platform name.
        from_date: Start of date range (ISO 8601).
        to_date: End of date range (ISO 8601).
        limit: Max results (default 20, max 50).
        offset: Pagination offset.
    """
    try:
        capped_limit = min(limit, 50)
        return await _client().get(
            "/v1/posts",
            status=status,
            platform=platform,
            fromDate=from_date,
            toDate=to_date,
            limit=capped_limit,
            offset=offset,
        )
    except ZernioAPIError as e:
        return _error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def posts_delete(post_id: str) -> dict:
    """Delete a draft or scheduled post.

    Use for draft or scheduled posts only. For published posts, use
    posts_unpublish instead. If you don't know the post's status, call
    posts_get first.
    """
    try:
        # Server-side guard: check status before deleting
        post = await _client().get(f"/v1/posts/{post_id}")
        post_data = post.get("post", post)
        post_status = post_data.get("status", "")
        if post_status in ("published",):
            return _error(
                "Cannot delete a published post. Use posts_unpublish instead "
                "to remove it from the platform while keeping the Zernio record."
            )
        return await _client().delete(f"/v1/posts/{post_id}")
    except ZernioAPIError as e:
        return _error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def posts_unpublish(post_id: str) -> dict:
    """Remove a published post from the social media platform.

    Keeps the Zernio record but deletes the post from the platform
    (e.g., deletes the tweet from Twitter). For drafts or scheduled posts,
    use posts_delete instead. If you don't know the post's status, call
    posts_get first.
    """
    try:
        post = await _client().get(f"/v1/posts/{post_id}")
        post_data = post.get("post", post)
        post_status = post_data.get("status", "")
        if post_status in ("draft", "scheduled"):
            return _error(
                f"Cannot unpublish a {post_status} post. Use posts_delete instead."
            )
        return await _client().post(f"/v1/posts/{post_id}/unpublish")
    except ZernioAPIError as e:
        return _error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
async def posts_retry(post_id: str) -> dict:
    """Retry a failed post.

    Before retrying, call posts_get to check failure_reason and confirm with
    the user that the underlying issue has been resolved (e.g., image resized,
    caption shortened, account reconnected).
    """
    try:
        return await _client().post(f"/v1/posts/{post_id}/retry")
    except ZernioAPIError as e:
        return _error(e.message)


# ---------------------------------------------------------------------------
# 3. Media Upload (1 tool)
# ---------------------------------------------------------------------------


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
async def media_upload(
    url: str | None = None,
    base64_data: str | None = None,
    mime_type: str | None = None,
    file_name: str = "upload",
) -> dict:
    """Upload media for use in posts. Returns publicUrl to pass to posts_create.

    Two input modes:
      - URL (preferred): provide a publicly accessible HTTPS URL.
        The server fetches the file and uploads it via Zernio's presigned flow.
      - Base64 (for mobile camera roll, images under 2MB only):
        provide base64_data and mime_type (e.g., "image/png").

    For larger files or videos, provide a URL.

    Supported formats: JPG, PNG, WebP, GIF, MP4, MOV, WebM.

    Args:
        url: Publicly accessible HTTPS URL to the media file.
        base64_data: Base64-encoded file content (images under 2MB only).
        mime_type: MIME type when using base64_data (e.g., "image/png").
        file_name: Optional filename for the upload.
    """
    client = _client()

    try:
        if url:
            # URL path: fetch → presign → upload to GCS
            data, content_type = await client.fetch_url_bytes(url)
            ext = content_type.split("/")[-1].replace("quicktime", "mov")
            fname = f"{file_name}.{ext}"

            presign = await client.presign_media(fname, content_type)
            await client.upload_to_gcs(presign["uploadUrl"], data, content_type)
            return {"publicUrl": presign["publicUrl"]}

        elif base64_data and mime_type:
            # Base64 path: decode → presign → upload to GCS
            if mime_type.lower() not in ALLOWED_MEDIA_TYPES:
                return _error(
                    f"Unsupported MIME type: {mime_type}. "
                    f"Supported: {', '.join(sorted(ALLOWED_MEDIA_TYPES))}"
                )
            try:
                raw = base64.b64decode(base64_data)
            except Exception:
                return _error("Invalid base64 data")

            if len(raw) > MAX_BASE64_BYTES:
                return _error(
                    f"Image exceeds 2MB base64 limit ({len(raw) / 1024 / 1024:.1f}MB). "
                    "Please provide a URL instead."
                )

            ext = mime_type.split("/")[-1].replace("quicktime", "mov")
            fname = f"{file_name}.{ext}"

            presign = await client.presign_media(fname, mime_type)
            await client.upload_to_gcs(presign["uploadUrl"], raw, mime_type)
            return {"publicUrl": presign["publicUrl"]}

        else:
            return _error(
                "Provide either 'url' (HTTPS link) or 'base64_data' + 'mime_type' "
                "(for images under 2MB from mobile camera roll)."
            )

    except SSRFError as e:
        return _error(str(e))
    except ZernioAPIError as e:
        return _error(e.message)


# ---------------------------------------------------------------------------
# 4. Analytics (2 tools)
# ---------------------------------------------------------------------------

_ORIGIN_MAP = {"all": "all", "via_zernio": "late", "imported": "imported"}


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def analytics_posts(
    post_id: str | None = None,
    platform: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = 10,
) -> dict:
    """Get per-post engagement metrics (likes, comments, shares, impressions).

    Without post_id: returns paginated list sorted by engagement.
    With post_id: returns engagement timeline for that specific post.

    Results include human-readable platform names and platformPostUrl.

    Args:
        post_id: Optional. Get timeline for a specific post.
        platform: Filter by platform name.
        from_date: Start of date range (ISO 8601).
        to_date: End of date range (ISO 8601).
        limit: Max results (default 10, max 50).
    """
    try:
        if post_id:
            return await _client().get(
                f"/v1/analytics/post-timeline",
                postId=post_id,
            )
        return await _client().get(
            "/v1/analytics",
            platform=platform,
            fromDate=from_date,
            toDate=to_date,
            limit=min(limit, 50),
        )
    except ZernioAPIError as e:
        return _error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def analytics_insights(
    type: Literal["best_time", "content_decay", "daily_metrics", "posting_frequency"],
    platform: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    origin: Literal["all", "via_zernio", "imported"] = "all",
) -> dict:
    """Get aggregated analytics insights.

    Type guide:
      - best_time: When to post for maximum engagement (day + hour data)
      - content_decay: How fast posts lose reach on each platform
      - daily_metrics: Day-by-day volume and engagement overview
      - posting_frequency: Optimal posts-per-week cadence

    Use best_time when asked "when should I post?"
    Use content_decay when asked "how long do my posts stay relevant?"
    Use daily_metrics for "how are my posts doing?" overviews.
    Use posting_frequency when asked "am I posting enough?"

    Args:
        type: The type of insight to retrieve.
        platform: Filter by platform name.
        from_date: Start of date range (ISO 8601).
        to_date: End of date range (ISO 8601).
        origin: Filter by post origin: "all", "via_zernio", or "imported".
    """
    endpoint_map = {
        "best_time": "/v1/analytics/best-time",
        "content_decay": "/v1/analytics/content-decay",
        "daily_metrics": "/v1/analytics/daily-metrics",
        "posting_frequency": "/v1/analytics/posting-frequency",
    }
    try:
        return await _client().get(
            endpoint_map[type],
            platform=platform,
            fromDate=from_date,
            toDate=to_date,
            source=_ORIGIN_MAP.get(origin, "all"),
        )
    except ZernioAPIError as e:
        return _error(e.message)


# ---------------------------------------------------------------------------
# 5. Queue (1 tool)
# ---------------------------------------------------------------------------


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def queue_preview(
    profile_id: str,
    limit: int = 5,
) -> dict:
    """Preview upcoming queue slots for scheduling context.

    Returns the next N queue slots with datetime (ISO 8601), platform, and
    whether the slot is occupied or open.

    Present a maximum of 3 suggested open slots in natural language before
    asking the user to choose, not the entire queue.

    Args:
        profile_id: The profile to check queue slots for.
        limit: Number of slots to return (default 5).
    """
    try:
        return await _client().get(
            "/v1/queue/preview",
            profileId=profile_id,
            limit=limit,
        )
    except ZernioAPIError as e:
        return _error(e.message)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    if settings.mcp_transport == "http":
        mcp.run(transport="streamable-http", host=settings.host, port=settings.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
