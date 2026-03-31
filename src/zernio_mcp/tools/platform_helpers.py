"""Platform helpers: Reddit, LinkedIn, Pinterest, YouTube specific tools."""

from __future__ import annotations

from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError, cache_get, cache_set
from zernio_mcp.tools._common import client, error


# --- Reddit ---

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def reddit_search(query: str, subreddit: str | None = None, limit: int = 20) -> dict:
    """Search Reddit posts.

    Args:
        query: Search query string.
        subreddit: Optional. Limit search to a specific subreddit.
        limit: Max results (default 20).
    """
    try:
        return await client().get("/v1/reddit/search", query=query, subreddit=subreddit, limit=limit)
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def reddit_feed(subreddit: str, limit: int = 20) -> dict:
    """Get a subreddit's feed (recent posts).

    Args:
        subreddit: Subreddit name (without r/).
        limit: Max results (default 20).
    """
    try:
        return await client().get("/v1/reddit/feed", subreddit=subreddit, limit=limit)
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def reddit_subreddits(account_id: str) -> dict:
    """List the user's joined subreddits. Call this before reddit_flairs to find subreddit names.

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


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def reddit_flairs(account_id: str, subreddit: str) -> dict:
    """Get available flairs for a subreddit. Call reddit_subreddits first to find subreddit names.

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

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def linkedin_mentions(account_id: str) -> dict:
    """Get recent LinkedIn mentions of the user or organization.

    Args:
        account_id: LinkedIn account ID.
    """
    try:
        return await client().get(f"/v1/accounts/{account_id}/linkedin-mentions")
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def linkedin_org_analytics(account_id: str) -> dict:
    """Get LinkedIn organization analytics — follower growth, impressions, engagement.

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

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def pinterest_boards(account_id: str) -> dict:
    """List Pinterest boards with names and pin counts.

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

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def youtube_playlists(account_id: str) -> dict:
    """List YouTube playlists with titles and video counts.

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
