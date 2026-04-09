"""Post tools: create, get, list, delete, unpublish, retry, update, bulk upload."""

from __future__ import annotations

from typing import Literal

from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError
from zernio_mcp.tools._common import client, error


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
async def posts_create(
    content: str,
    platforms: list[dict],
    publish_now: bool = False,
    scheduled_for: str | None = None,
    media_items: list[dict] | None = None,
    profile_id: str | None = None,
) -> dict:
    """[social] Create a social media post (draft, scheduled, or immediate publish).

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
        platforms: Platform targets. Each platform object must include 'accountId' (str) and may include platform-specific options. Example: [{'accountId': 'acc_123'}].
        publish_now: Publish immediately if True.
        scheduled_for: ISO 8601 datetime for scheduled publishing.
        media_items: Media attachments, each {"url": "...", "type": "image"|"video"}.
        profile_id: Optional profile for brand context.
    """
    try:
        body: dict = {"content": content, "platforms": platforms}
        if scheduled_for:
            body["scheduledFor"] = scheduled_for
        elif publish_now:
            body["publishNow"] = True
        if media_items:
            body["mediaItems"] = media_items
        if profile_id:
            body["profileId"] = profile_id
        return await client().post("/v1/posts", body)
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def posts_get(post_id: str) -> dict:
    """[social] Get a single post by ID, including status, platformPostUrl, and failure_reason.

    Use this to check post status after creation. For failed posts, the response
    includes failure_reason (e.g., "Image aspect ratio rejected").
    """
    try:
        return await client().get(f"/v1/posts/{post_id}")
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def posts_list(
    status: Literal["draft", "scheduled", "published", "failed"] | None = None,
    platform: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """[social] List posts with optional filters.

    Filter by status (draft, scheduled, published, failed), platform, or
    date range (ISO 8601). To see failed posts: posts_list(status="failed")
    """
    try:
        return await client().get(
            "/v1/posts", status=status, platform=platform,
            fromDate=from_date, toDate=to_date,
            limit=min(limit, 50), offset=offset,
        )
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def posts_delete(post_id: str) -> dict:
    """[social] Delete a draft or scheduled post. For published posts, use posts_unpublish."""
    try:
        return await client().delete(f"/v1/posts/{post_id}")
    except ZernioAPIError as e:
        if e.status_code in (409, 422) or "published" in e.message.lower():
            return error("Cannot delete a published post. Use posts_unpublish instead.")
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def posts_unpublish(post_id: str) -> dict:
    """[social] Remove a published post from the platform. For drafts, use posts_delete."""
    try:
        return await client().post(f"/v1/posts/{post_id}/unpublish")
    except ZernioAPIError as e:
        if e.status_code in (409, 422) or "draft" in e.message.lower() or "scheduled" in e.message.lower():
            return error("Cannot unpublish a draft or scheduled post. Use posts_delete instead.")
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
async def posts_retry(post_id: str) -> dict:
    """[social] Retry a failed post. Call posts_get first to check failure_reason."""
    try:
        return await client().post(f"/v1/posts/{post_id}/retry")
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def posts_update(
    post_id: str,
    content: str | None = None,
    platforms: list[dict] | None = None,
    media_items: list[dict] | None = None,
    scheduled_for: str | None = None,
) -> dict:
    """[social] Edit a draft or scheduled post.

    Only draft and scheduled posts can be edited. Published posts cannot be modified.

    Args:
        post_id: The post to update.
        content: New post text content.
        platforms: Updated platform targets.
        media_items: Media attachments, each {"url": "...", "type": "image"|"video"}.
        scheduled_for: New scheduled datetime (ISO 8601).
    """
    try:
        body: dict = {}
        if content is not None:
            body["content"] = content
        if platforms is not None:
            body["platforms"] = platforms
        if media_items is not None:
            body["mediaItems"] = media_items
        if scheduled_for is not None:
            body["scheduledFor"] = scheduled_for
        return await client().put(f"/v1/posts/{post_id}", body)
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
async def posts_bulk_upload(csv_content: str) -> dict:
    """[social] Import multiple posts from CSV data.

    Use for 5 or more posts at once. For fewer posts, use posts_create individually.
    Returns a summary with created count, failed count, and any errors per row.

    Args:
        csv_content: CSV string with post data (headers: content, platform, scheduledFor, etc.).
    """
    try:
        return await client().post("/v1/posts/bulk-upload", {"csv": csv_content})
    except ZernioAPIError as e:
        return error(e.message)
