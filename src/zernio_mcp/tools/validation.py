"""Validation tools: post length, full post, media validation."""

from __future__ import annotations

from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError
from zernio_mcp.tools._common import client, error


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def validate_post_length(
    text: str | None = None,
    platform: str = "",
    content: str | None = None,
) -> dict:
    """[social] Quick text-only check: does this content fit the platform's character limit?

    Fast pre-flight check — no media validation. Returns valid/invalid with
    remaining character count or overage.

    ## Supported platforms

    Character limits vary per platform. Common: twitter (280), bluesky (300),
    instagram (2200 caption), linkedin (3000), facebook (63206), threads (500),
    tiktok (2200 caption), youtube (5000 description).

    Args:
        text: The post text to validate. Preferred parameter name (matches Zernio API).
        platform: Target platform (e.g., "twitter", "instagram", "linkedin").
        content: Deprecated alias for ``text``. Accepted for backwards compatibility.
    """
    # Accept either ``text`` (preferred, matches Zernio API) or ``content``
    # (legacy alias used by earlier MCP releases). See CDI-906.
    payload_text = text if text is not None else content
    if payload_text is None:
        return error("validate_post_length requires the 'text' parameter (or legacy alias 'content').")
    if not platform:
        return error("validate_post_length requires the 'platform' parameter.")
    try:
        return await client().post("/v1/tools/validate/post-length", {
            "text": payload_text, "platform": platform,
        })
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def validate_post(
    content: str,
    platforms: list[dict],
    media_urls: list[str] | None = None,
) -> dict:
    """[social] Full pre-flight validation: content + media + platform config.

    Validates everything before posting — character limits, media dimensions,
    platform-specific requirements. Returns per-platform validation results.

    ## Supported platforms (CDI-1063)

    Each entry in ``platforms`` must include ``platform`` and ``accountId``.
    Supported platform identifiers: ``twitter``, ``bluesky``, ``linkedin``,
    ``facebook``, ``instagram``, ``threads``, ``tiktok``, ``youtube``,
    ``pinterest``, ``reddit``. Validation enforces per-platform quirks such
    as Instagram/TikTok's media requirement, YouTube's video-only rule, and
    each platform's character limit (Twitter 280, Bluesky 300, LinkedIn
    3000, Threads 500, etc.).

    Args:
        content: Post text content.
        platforms: Platform targets (same format as posts_create).
        media_urls: Optional media URLs to validate.
    """
    try:
        body: dict = {"content": content, "platforms": platforms}
        if media_urls:
            body["mediaItems"] = [{"url": u} for u in media_urls]
        return await client().post("/v1/tools/validate/post", body)
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def validate_media(media_url: str, platform: str) -> dict:
    """[social] Validate media dimensions, format, and size against platform requirements.

    Args:
        media_url: URL of the media to validate.
        platform: Target platform (e.g., "instagram", "twitter").
    """
    try:
        return await client().post("/v1/tools/validate/media", {
            "url": media_url, "platform": platform,
        })
    except ZernioAPIError as e:
        return error(e.message)
