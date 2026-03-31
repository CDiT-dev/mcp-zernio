"""Validation tools: post length, full post, media validation."""

from __future__ import annotations

from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError
from zernio_mcp.tools._common import client, error


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def validate_post_length(content: str, platform: str) -> dict:
    """Quick text-only check: does this content fit the platform's character limit?

    Fast pre-flight check — no media validation. Returns valid/invalid with
    remaining character count or overage.

    Args:
        content: The post text to validate.
        platform: Target platform (e.g., "twitter", "instagram", "linkedin").
    """
    try:
        return await client().post("/v1/tools/validate/post-length", {
            "content": content, "platform": platform,
        })
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def validate_post(
    content: str,
    platforms: list[dict],
    media_urls: list[str] | None = None,
) -> dict:
    """Full pre-flight validation: content + media + platform config.

    Validates everything before posting — character limits, media dimensions,
    platform-specific requirements. Returns per-platform validation results.

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
    """Validate media dimensions, format, and size against platform requirements.

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
