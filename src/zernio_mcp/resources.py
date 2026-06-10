"""MCP resources: reference/context data served under the ``zernio://`` scheme.

Exposing this as resources (instead of restating it as prose in every tool
docstring) lets the model resolve platform limits and account/profile ids
without spending a tool call — a real round-trip win on a surface where almost
everything needs an accountId first.
"""

from __future__ import annotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError
from zernio_mcp.tools._common import client


# ---------------------------------------------------------------------------
# Static taxonomy: per-platform capabilities and character limits
# ---------------------------------------------------------------------------

# Canonical source for the per-platform guidance scattered across the
# posts_create / validate_* / queue_create_slot docstrings. Character limits are
# the practical caption/description limits Zernio validates against.
PLATFORMS: dict[str, dict] = {
    "twitter": {
        "char_limit": 280,
        "media_required": False,
        "video_only": False,
        "supports_threads": True,
        "notes": "Threads supported (use thread_items).",
    },
    "bluesky": {
        "char_limit": 300,
        "media_required": False,
        "video_only": False,
        "supports_threads": True,
        "notes": "Threads supported (use thread_items).",
    },
    "linkedin": {
        "char_limit": 3000,
        "media_required": False,
        "video_only": False,
        "supports_threads": False,
        "notes": "Connected account may be personal or organization.",
    },
    "facebook": {
        "char_limit": 63206,
        "media_required": False,
        "video_only": False,
        "supports_threads": False,
        "notes": "Publishes to the Page on the connected account; personal profiles unsupported.",
    },
    "instagram": {
        "char_limit": 2200,
        "media_required": True,
        "video_only": False,
        "supports_threads": False,
        "notes": "Requires at least one media item; text-only posts are rejected.",
    },
    "threads": {
        "char_limit": 500,
        "media_required": False,
        "video_only": False,
        "supports_threads": False,
        "notes": "Meta 'Threads' does NOT support native API threading despite the name.",
    },
    "tiktok": {
        "char_limit": 2200,
        "media_required": True,
        "video_only": False,
        "supports_threads": False,
        "notes": "Requires at least one media item.",
    },
    "youtube": {
        "char_limit": 5000,
        "media_required": True,
        "video_only": True,
        "supports_threads": False,
        "notes": "Requires a video media item (description limit shown).",
    },
    "pinterest": {
        "char_limit": 500,
        "media_required": True,
        "video_only": False,
        "supports_threads": False,
        "notes": "Pin to a board; media required.",
    },
    "reddit": {
        "char_limit": 40000,
        "media_required": False,
        "video_only": False,
        "supports_threads": False,
        "notes": "Subreddit + flair may be required; see reddit_subreddits / reddit_flairs.",
    },
}


@mcp.resource(
    "zernio://platforms",
    name="Supported platforms",
    title="Supported platforms & character limits",
    mime_type="application/json",
    tags={"social", "reference", "platforms"},
)
def platforms_resource() -> dict:
    """Per-platform character limits and capability flags.

    Use this to pick character limits and detect platform quirks (media
    required, video-only, native thread support) before calling posts_create or
    the validate_* tools — no tool round-trip needed.
    """
    return {
        "platforms": PLATFORMS,
        "thread_platforms": [p for p, v in PLATFORMS.items() if v["supports_threads"]],
        "media_required_platforms": [p for p, v in PLATFORMS.items() if v["media_required"]],
    }


@mcp.resource(
    "zernio://accounts",
    name="Connected accounts",
    title="Connected social accounts",
    mime_type="application/json",
    tags={"social", "reference", "accounts"},
)
async def accounts_resource() -> dict:
    """Live list of connected accounts (id, platform, username, profile).

    Resolve accountId values here instead of spending an accounts_list tool
    call. Served from the same 60s TTL cache the tool uses; PII is stripped.
    """
    from zernio_mcp.tools.accounts import accounts_list

    return await accounts_list()


@mcp.resource(
    "zernio://profiles",
    name="Brand profiles",
    title="Brand profiles",
    mime_type="application/json",
    tags={"social", "reference", "profiles"},
)
async def profiles_resource() -> dict:
    """Live list of brand profiles and their account groupings.

    Resolve profileId values here (for posts_create / queue tools) instead of
    spending a profiles_list tool call. Served from the 60s TTL cache.
    """
    from zernio_mcp.tools.profiles import profiles_list

    return await profiles_list()


@mcp.resource(
    "zernio://usage",
    name="Usage stats",
    title="API usage & billing snapshot",
    mime_type="application/json",
    tags={"social", "reference", "usage"},
)
async def usage_resource() -> dict:
    """Current API usage counts, post counts, and billing info.

    Read this for context before bulk operations rather than calling
    usage_stats as a tool.
    """
    try:
        return await client().get("/v1/usage-stats")
    except ZernioAPIError as e:
        return {"error": e.message}
