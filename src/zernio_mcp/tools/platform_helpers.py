"""Platform helpers: Reddit, LinkedIn, Pinterest, YouTube specific tools."""

from __future__ import annotations

from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError, cache_get, cache_set
from zernio_mcp.tools._common import client, error


# --- Reddit ---

@mcp.tool(
    title="Reddit search",
    tags={"social", "reddit", "read"},
    annotations=ToolAnnotations(title="Reddit search", readOnlyHint=True, idempotentHint=True, openWorldHint=True),
)
async def reddit_search(query: str, subreddit: str | None = None, limit: int = 20) -> dict:
    """[social] Search Reddit posts.

    Args:
        query: Search query string.
        subreddit: Optional. Limit search to a specific subreddit.
        limit: Max results (default 20).
    """
    try:
        return await client().get("/v1/reddit/search", query=query, subreddit=subreddit, limit=limit)
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(
    title="Reddit feed",
    tags={"social", "reddit", "read"},
    annotations=ToolAnnotations(title="Reddit feed", readOnlyHint=True, idempotentHint=True, openWorldHint=True),
)
async def reddit_feed(subreddit: str, limit: int = 20) -> dict:
    """[social] Get a subreddit's feed (recent posts).

    Args:
        subreddit: Subreddit name (without r/).
        limit: Max results (default 20).
    """
    try:
        return await client().get("/v1/reddit/feed", subreddit=subreddit, limit=limit)
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(
    title="Reddit subreddits",
    tags={"social", "reddit", "read"},
    annotations=ToolAnnotations(title="Reddit subreddits", readOnlyHint=True, idempotentHint=True, openWorldHint=True),
)
async def reddit_subreddits(account_id: str) -> dict:
    """[social] List the user's joined subreddits. Call this before reddit_flairs to find subreddit names.

    Args:
        account_id: Reddit account ID.
    """
    cache_key = f"reddit_subs_{account_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    try:
        result = await client().get(f"/v1/accounts/{account_id}/reddit-subreddits")
        cache_set(cache_key, result)
        return result
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(
    title="Reddit flairs",
    tags={"social", "reddit", "read"},
    annotations=ToolAnnotations(title="Reddit flairs", readOnlyHint=True, idempotentHint=True, openWorldHint=True),
)
async def reddit_flairs(account_id: str, subreddit: str) -> dict:
    """[social] Get available flairs for a subreddit. Call reddit_subreddits first to find subreddit names.

    Args:
        account_id: Reddit account ID.
        subreddit: Subreddit name.
    """
    cache_key = f"reddit_flairs_{account_id}_{subreddit}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    try:
        result = await client().get(f"/v1/accounts/{account_id}/reddit-flairs", subreddit=subreddit)
        cache_set(cache_key, result)
        return result
    except ZernioAPIError as e:
        return error(e.message)


# --- LinkedIn ---

@mcp.tool(
    title="Linkedin mentions",
    tags={"social", "linkedin", "read"},
    annotations=ToolAnnotations(title="Linkedin mentions", readOnlyHint=True, idempotentHint=True, openWorldHint=True),
)
async def linkedin_mentions(account_id: str) -> dict:
    """[social] Get recent LinkedIn mentions of the user or organization.

    Args:
        account_id: LinkedIn account ID.
    """
    try:
        return await client().get(f"/v1/accounts/{account_id}/linkedin-mentions")
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(
    title="Linkedin org analytics",
    tags={"social", "linkedin", "read"},
    annotations=ToolAnnotations(title="Linkedin org analytics", readOnlyHint=True, idempotentHint=True, openWorldHint=True),
)
async def linkedin_org_analytics(account_id: str) -> dict:
    """[social] Get LinkedIn organization analytics — follower growth, impressions, engagement.

    Args:
        account_id: LinkedIn organization account ID.
    """
    cache_key = f"li_org_{account_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    try:
        result = await client().get(f"/v1/accounts/{account_id}/linkedin-aggregate-analytics")
        cache_set(cache_key, result, ttl=300.0)
        return result
    except ZernioAPIError as e:
        return error(e.message)


# --- Pinterest ---

@mcp.tool(
    title="Pinterest boards",
    tags={"social", "pinterest", "read"},
    annotations=ToolAnnotations(title="Pinterest boards", readOnlyHint=True, idempotentHint=True, openWorldHint=True),
)
async def pinterest_boards(account_id: str) -> dict:
    """[social] List Pinterest boards with names and pin counts.

    Args:
        account_id: Pinterest account ID.
    """
    cache_key = f"pin_boards_{account_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    try:
        result = await client().get(f"/v1/accounts/{account_id}/pinterest-boards")
        cache_set(cache_key, result)
        return result
    except ZernioAPIError as e:
        return error(e.message)


# --- YouTube ---

@mcp.tool(
    title="Youtube playlists",
    tags={"social", "youtube", "read"},
    annotations=ToolAnnotations(title="Youtube playlists", readOnlyHint=True, idempotentHint=True, openWorldHint=True),
)
async def youtube_playlists(account_id: str) -> dict:
    """[social] List YouTube playlists with titles and video counts.

    Args:
        account_id: YouTube account ID.
    """
    cache_key = f"yt_playlists_{account_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    try:
        result = await client().get(f"/v1/accounts/{account_id}/youtube-playlists")
        cache_set(cache_key, result)
        return result
    except ZernioAPIError as e:
        return error(e.message)
