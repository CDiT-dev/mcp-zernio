"""Post tools: create, get, list, delete, unpublish, retry, update, bulk upload."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field
from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError
from zernio_mcp.tools._common import client, error


class MediaItem(BaseModel):
    """A media attachment for a post or thread item."""
    url: str = Field(description="Public HTTPS URL of the media file.")
    type: Literal["image", "video"] = Field(description="Media type.")


class ThreadItem(BaseModel):
    """A single post within a thread. Max 280 chars for Twitter/X, 300 for Bluesky."""
    content: Annotated[str, Field(
        max_length=300,
        description="Post text. Max 280 chars for Twitter/X, 300 for Bluesky.",
    )]
    media_items: list[MediaItem] | None = Field(
        default=None,
        description="Optional media attachments for this thread item.",
    )


_THREAD_PLATFORMS = {"twitter", "bluesky"}


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
async def posts_create(
    content: str | None = None,
    platforms: list[dict] | None = None,
    publish_now: bool = False,
    scheduled_for: str | None = None,
    media_items: list[MediaItem] | None = None,
    profile_id: str | None = None,
    thread_items: Annotated[list[ThreadItem], Field(min_length=2, max_length=25)] | None = None,
) -> dict:
    """[social] Create a social media post or thread (draft, scheduled, or immediate).

    Three modes:
      - Draft (default): omit publish_now and scheduled_for
      - Immediate: publish_now=True
      - Scheduled: scheduled_for="2026-04-01T09:00:00Z" (ISO 8601)

    ## Single post
    Pass content with your text. Optionally attach media_items.

    ## Thread (Twitter/X and Bluesky only)
    Pass thread_items instead of content. thread_items is mutually exclusive
    with top-level content and media_items.

    Splitting guidance: the first item should work as a standalone hook —
    assume readers may only see it before deciding to engage. Break subsequent
    items at natural sentence or paragraph boundaries so each reads as a
    complete thought. Do not add numbering (1/, 2/, etc.) — the platform
    displays threads as connected posts. Keep each item well under the
    character limit rather than packing to the max.

    Example:
      thread_items=[
          {"content": "We just launched a new feature that changes how you manage your posts."},
          {"content": "Here's what it looks like in action.", "media_items": [{"url": "https://...", "type": "image"}]},
      ]

    Character limits per item: Twitter/X 280, Bluesky 300.
    Min 2 items, max 25 items per thread.

    Get account IDs first via accounts_list. Each entry in platforms requires:
      {"platform": "twitter", "accountId": "acc_123"}

    For cross-posting, include multiple entries in the platforms array.
    When cross-posting, verify each platform's status in the response —
    partial failures are possible (e.g., Twitter succeeds but Instagram fails).

    If the user has multiple accounts for the target platform and hasn't
    specified which one, call profiles_list first to identify the correct
    brand context, then confirm before posting.

    Args:
        content: Post text content. Omit when using thread_items.
        platforms: Platform targets. Each must include 'platform' and 'accountId'. Example: [{"platform": "twitter", "accountId": "acc_123"}].
        publish_now: Publish immediately if True.
        scheduled_for: ISO 8601 datetime for scheduled publishing.
        media_items: Media attachments for a single post. Mutually exclusive with thread_items.
        profile_id: Profile ID for brand context (from profiles_list). Required when the user has multiple accounts for the same platform to select the correct brand.
        thread_items: Thread posts for Twitter/X and Bluesky only — other platforms will be rejected. Mutually exclusive with content and media_items. Min 2, max 25 items.
    """
    try:
        platforms = platforms or []

        if thread_items is not None:
            if content:
                return error("thread_items is mutually exclusive with top-level content. Omit content when posting a thread.")
            if media_items:
                return error("thread_items is mutually exclusive with top-level media_items. Put media inside each thread item instead.")
            # Runtime fallbacks — schema Field(min_length/max_length) catches these
            # at the MCP protocol layer, but direct callers bypass schema validation.
            if len(thread_items) < 2:
                return error("thread_items must contain at least 2 items — a single item is just a regular post.")
            if len(thread_items) > 25:
                return error("thread_items supports a maximum of 25 items per thread.")

            platform_names = {p.get("platform", "") for p in platforms}
            unsupported = platform_names - _THREAD_PLATFORMS
            if unsupported:
                return error(
                    f"Threads are only supported on twitter and bluesky. "
                    f"Unsupported platforms: {', '.join(sorted(unsupported))}"
                )

            api_thread_items = []
            for item in thread_items:
                api_item: dict = {"content": item.content}
                if item.media_items:
                    api_item["mediaItems"] = [m.model_dump() for m in item.media_items]
                api_thread_items.append(api_item)

            for p in platforms:
                p.setdefault("platformSpecificData", {})
                p["platformSpecificData"]["threadItems"] = api_thread_items

            # Zernio API requires top-level content; empty string signals thread mode
            body: dict = {"content": "", "platforms": platforms}
        else:
            body = {"content": content or "", "platforms": platforms}

        if scheduled_for:
            body["scheduledFor"] = scheduled_for
        elif publish_now:
            body["publishNow"] = True
        if media_items and thread_items is None:
            body["mediaItems"] = [m.model_dump() for m in media_items]
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
        # Pre-check: the API returns inconsistent errors for wrong-status deletes
        post = await client().get(f"/v1/posts/{post_id}")
        status = post.get("post", {}).get("status", "")
        if status == "published":
            return error("Cannot delete a published post. Use posts_unpublish instead.")
        return await client().delete(f"/v1/posts/{post_id}")
    except ZernioAPIError as e:
        if e.status_code == 404:
            return error(f"Post {post_id} not found.")
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def posts_unpublish(post_id: str) -> dict:
    """[social] Remove a published post from the platform. For drafts, use posts_delete."""
    try:
        # Pre-check: the API returns 500 instead of a clear error for non-published posts
        post = await client().get(f"/v1/posts/{post_id}")
        status = post.get("post", {}).get("status", "")
        if status in ("draft", "scheduled"):
            return error(f"Cannot unpublish a {status} post. Use posts_delete instead.")
        if status == "failed":
            return error("Cannot unpublish a failed post. Use posts_retry or posts_delete instead.")
        return await client().post(f"/v1/posts/{post_id}/unpublish")
    except ZernioAPIError as e:
        if e.status_code == 404:
            return error(f"Post {post_id} not found.")
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
    media_items: list[MediaItem] | None = None,
    scheduled_for: str | None = None,
) -> dict:
    """[social] Edit a draft or scheduled post.

    Only draft and scheduled posts can be edited. Published posts cannot be modified.

    Args:
        post_id: The post to update.
        content: New post text content.
        platforms: Updated platform targets.
        media_items: Media attachments.
        scheduled_for: New scheduled datetime (ISO 8601).
    """
    try:
        body: dict = {}
        if content is not None:
            body["content"] = content
        if platforms is not None:
            body["platforms"] = platforms
        if media_items is not None:
            body["mediaItems"] = [m.model_dump() for m in media_items]
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
