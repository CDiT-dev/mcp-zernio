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

    ## Supported platforms (CDI-1063)

    Pass platform identifiers in each ``platforms`` entry: ``twitter``,
    ``bluesky``, ``linkedin``, ``facebook``, ``instagram``, ``threads``,
    ``tiktok``, ``youtube``, ``pinterest``, ``reddit``. Platform quirks:

    * ``facebook`` posts publish to the Page configured on the connected
      account; personal Facebook profiles are not supported.
    * ``linkedin`` accounts can be personal or organization — the connected
      account decides which.
    * ``instagram`` and ``tiktok`` require at least one media item; text-only
      posts are rejected by those platforms.
    * ``youtube`` requires a video media item.
    * Character limits vary widely — run ``validate_post_length`` /
      ``validate_post`` first to avoid platform-specific 400s.

    ## Single post
    Pass content with your text. Optionally attach media_items.

    ## Thread (Twitter/X and Bluesky only)
    Note: the "Threads" platform (Meta) does NOT support native threading
    via the API despite its name. Only twitter and bluesky support threads.
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

            # Zernio treats the top-level post as the lead of the thread; the
            # follow-up posts go into platformSpecificData.threadItems. Sending
            # an empty top-level content is rejected with 400.
            lead_item, *follow_items = thread_items

            api_thread_items = []
            for item in follow_items:
                api_item: dict = {"content": item.content}
                if item.media_items:
                    api_item["mediaItems"] = [m.model_dump() for m in item.media_items]
                api_thread_items.append(api_item)

            for p in platforms:
                p.setdefault("platformSpecificData", {})
                p["platformSpecificData"]["threadItems"] = api_thread_items

            body: dict = {"content": lead_item.content, "platforms": platforms}
            if lead_item.media_items:
                body["mediaItems"] = [m.model_dump() for m in lead_item.media_items]
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

    ## Draft → scheduled transition (CDI-1004)

    Passing ``scheduled_for`` on a *draft* now promotes the post to
    ``status: "scheduled"`` in the same call, so the scheduler picks it up.
    Earlier versions stored the new timestamp but left the post as a draft,
    causing it to never auto-publish. If you only need to reschedule an
    already-scheduled post, the status stays ``"scheduled"``.

    Args:
        post_id: The post to update.
        content: New post text content.
        platforms: Updated platform targets.
        media_items: Media attachments.
        scheduled_for: New scheduled datetime (ISO 8601). On a draft post this
            also flips the status to "scheduled".
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
            # CDI-1004: the Zernio API stores scheduledFor without flipping
            # the post out of draft, so the scheduler never picks it up. Look
            # the current state up and include an explicit status transition
            # when promoting a draft.
            try:
                current = await client().get(f"/v1/posts/{post_id}")
                current_status = (current.get("post") or current).get("status", "")
                if current_status == "draft":
                    body["status"] = "scheduled"
            except ZernioAPIError:
                # If the read fails (e.g. 404), let the PUT surface the error.
                pass
        return await client().put(f"/v1/posts/{post_id}", body)
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def posts_schedule(post_id: str, scheduled_for: str) -> dict:
    """[social] Promote a draft post to scheduled at the given ISO 8601 datetime.

    Dedicated tool for the draft → scheduled transition documented in
    CDI-1004. Equivalent to ``posts_update(post_id, scheduled_for=...)`` on a
    draft, but explicit about intent and rejects already-published posts with
    a clear error.

    Args:
        post_id: The draft post to schedule.
        scheduled_for: ISO 8601 datetime to publish at (e.g. "2026-04-01T09:00:00Z").
    """
    if not scheduled_for:
        return error("posts_schedule requires 'scheduled_for' (ISO 8601 datetime).")
    try:
        current = await client().get(f"/v1/posts/{post_id}")
        status = (current.get("post") or current).get("status", "")
        if status == "published":
            return error("Cannot schedule a published post. Use posts_create for a new post.")
        if status == "failed":
            return error("Cannot schedule a failed post. Inspect with posts_get and use posts_retry instead.")
        return await client().put(
            f"/v1/posts/{post_id}",
            {"scheduledFor": scheduled_for, "status": "scheduled"},
        )
    except ZernioAPIError as e:
        if e.status_code == 404:
            return error(f"Post {post_id} not found.")
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
