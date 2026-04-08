"""Content research tools: download posts from any platform, YouTube transcript, Instagram hashtag, subreddit rules."""

from __future__ import annotations

from urllib.parse import urlparse

from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError
from zernio_mcp.tools._common import client, error

_PLATFORM_MAP = {
    "youtube.com": "youtube", "youtu.be": "youtube",
    "instagram.com": "instagram",
    "tiktok.com": "tiktok",
    "twitter.com": "twitter", "x.com": "twitter",
    "facebook.com": "facebook", "fb.com": "facebook",
    "linkedin.com": "linkedin",
    "bsky.app": "bluesky",
}


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def research_download_post(url: str) -> dict:
    """[social] Download post metadata from any supported platform using a post URL.

    Automatically detects the platform from the URL. Supports YouTube, Instagram,
    TikTok, Twitter/X, Facebook, LinkedIn, and Bluesky.

    Returns content text, media URLs, engagement metrics (likes, views, comments),
    and author info. For YouTube, also returns video title, channel name, and thumbnail.

    Args:
        url: Full post/video URL from any supported platform.
             e.g. "https://www.youtube.com/watch?v=abc123"
                  "https://www.tiktok.com/@user/video/123"
                  "https://twitter.com/user/status/123"
    """
    host = (urlparse(url).hostname or "").removeprefix("www.")
    platform = next((v for k, v in _PLATFORM_MAP.items() if host.endswith(k)), None)
    if not platform:
        return error(
            f"Cannot detect platform from URL: {url}. "
            "Supported: YouTube, Instagram, TikTok, Twitter/X, Facebook, LinkedIn, Bluesky"
        )
    try:
        return await client().get(f"/v1/tools/{platform}/download", url=url)
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def youtube_transcript(url: str) -> dict:
    """[social] Get a YouTube video's transcript text.

    Args:
        url: YouTube video URL.
    """
    try:
        return await client().get("/v1/tools/youtube/transcript", url=url)
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def instagram_hashtag(hashtag: str) -> dict:
    """[social] Check Instagram hashtag performance — usage count, related hashtags, competition level.

    Args:
        hashtag: The hashtag to check (without #).
    """
    try:
        return await client().post("/v1/tools/instagram/hashtag-checker", {"hashtag": hashtag})
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def reddit_subreddit_rules(subreddit: str) -> dict:
    """[social] Check subreddit posting rules, allowed content types, and flair requirements.

    Args:
        subreddit: Subreddit name (without r/).
    """
    try:
        return await client().get("/v1/tools/validate/subreddit", subreddit=subreddit)
    except ZernioAPIError as e:
        return error(e.message)
