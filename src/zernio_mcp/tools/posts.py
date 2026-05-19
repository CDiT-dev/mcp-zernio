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

    ## scheduled_for on a draft does NOT promote it (CDI-1004)

    Setting ``scheduled_for`` updates the timestamp stored on a draft, but
    Zernio's PUT endpoint does **not** transition the post to
    ``status: "scheduled"`` regardless of the body shape we send (verified
    against the live API for `status`, `state`, `lifecycle`, `publishNow`,
    and no extra field). The scheduler only picks up posts that were created
    with ``scheduledFor`` at creation time.

    To actually promote a draft to scheduled, use ``posts_schedule``, which
    delete-then-recreates the post with ``scheduledFor`` set (the post_id
    changes — see that tool's docstring).

    Args:
        post_id: The post to update.
        content: New post text content.
        platforms: Updated platform targets.
        media_items: Media attachments.
        scheduled_for: New scheduled datetime (ISO 8601). On an already-scheduled
            post this reschedules in place. On a draft this updates the stored
            timestamp but does NOT flip status — use ``posts_schedule`` for that.
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


def _extract_recreate_body(post: dict, scheduled_for: str) -> dict:
    """Build a posts_create-compatible body from an existing draft post.

    Preserves content, platforms (with platformSpecificData / threadItems
    where present), mediaItems, and profileId. The original ``_id`` is not
    carried over — the recreated post gets a fresh id.
    """
    body: dict = {
        "content": post.get("content", ""),
        "scheduledFor": scheduled_for,
    }
    raw_platforms = post.get("platforms") or []
    clean_platforms: list[dict] = []
    for entry in raw_platforms:
        # Strip per-platform status/result/timestamp fields. Keep wiring
        # fields that posts_create expects: platform, accountId,
        # platformSpecificData (incl. threadItems).
        platform = entry.get("platform")
        account = entry.get("accountId") or entry.get("account_id")
        if not platform or not account:
            continue
        cleaned: dict = {"platform": platform, "accountId": account}
        psd = entry.get("platformSpecificData")
        if psd:
            cleaned["platformSpecificData"] = psd
        clean_platforms.append(cleaned)
    body["platforms"] = clean_platforms

    media_items = post.get("mediaItems")
    if media_items:
        body["mediaItems"] = media_items

    # profileId on a post can be either a bare ObjectId string or a populated
    # subdocument {"_id": ..., "name": ...} (the GET response populates it).
    profile_id = post.get("profileId")
    if isinstance(profile_id, dict):
        profile_id = profile_id.get("_id")
    if profile_id:
        body["profileId"] = profile_id

    return body


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
async def posts_schedule(post_id: str, scheduled_for: str) -> dict:
    """[social] Promote a draft post to scheduled at the given ISO 8601 datetime.

    ## Behavior (CDI-1004 follow-up)

    Zernio's PUT endpoint cannot transition a draft to scheduled — it stores
    ``scheduledFor`` but silently keeps ``status: "draft"`` no matter which
    body shape we send. There is no dedicated transition endpoint either
    (``/schedule``, ``/publish``, ``/promote`` all 404).

    So this tool implements the transition as **delete-then-recreate**:

      1. GET the draft to capture content, platforms, mediaItems, profileId,
         and any platformSpecificData/threadItems.
      2. POST /v1/posts with those fields plus ``scheduledFor`` set.
      3. Only after the new post is confirmed created, DELETE the original.

    **The post_id changes.** The response is the new post (status=scheduled)
    and includes ``previous_post_id`` so callers can update any references
    they held. If the original delete fails after the recreate succeeds, the
    response still returns the new post but flags the orphaned original in
    ``orphaned_previous_post_id`` and ``warning``.

    Already-scheduled posts are rescheduled in place via PUT — no recreate
    needed, post_id is preserved.

    Args:
        post_id: The draft (or scheduled) post to schedule.
        scheduled_for: ISO 8601 datetime to publish at (e.g. "2026-04-01T09:00:00Z").
    """
    if not scheduled_for:
        return error("posts_schedule requires 'scheduled_for' (ISO 8601 datetime).")
    try:
        current = await client().get(f"/v1/posts/{post_id}")
        post = current.get("post") or current
        status = post.get("status", "")

        if status == "published":
            return error("Cannot schedule a published post. Use posts_create for a new post.")
        if status == "failed":
            return error("Cannot schedule a failed post. Inspect with posts_get and use posts_retry instead.")
        if status == "scheduled":
            # In-place reschedule works for already-scheduled posts.
            return await client().put(
                f"/v1/posts/{post_id}",
                {"scheduledFor": scheduled_for},
            )
        if status != "draft":
            return error(f"Cannot schedule post with status {status!r}.")

        # Draft → scheduled requires delete-then-recreate.
        recreate_body = _extract_recreate_body(post, scheduled_for)
        if not recreate_body.get("platforms"):
            return error(
                "Cannot schedule a draft with no platform targets. Use "
                "posts_update to add platforms first, then retry."
            )

        created = await client().post("/v1/posts", recreate_body)
        new_post = created.get("post") or created
        new_id = new_post.get("_id")
        if not new_id:
            return error("Recreate returned no post id — refusing to delete the original.")

        # Recreate succeeded — now safe to delete the original draft.
        try:
            await client().delete(f"/v1/posts/{post_id}")
        except ZernioAPIError as delete_err:
            # New post exists; original couldn't be deleted. Surface both.
            return {
                **created,
                "previous_post_id": post_id,
                "orphaned_previous_post_id": post_id,
                "warning": (
                    f"New scheduled post created ({new_id}), but failed to "
                    f"delete the original draft ({post_id}): "
                    f"{delete_err.message}. Delete it manually with posts_delete."
                ),
            }

        return {**created, "previous_post_id": post_id}
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
