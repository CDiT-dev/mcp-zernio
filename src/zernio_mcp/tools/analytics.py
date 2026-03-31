"""Analytics tools: per-post metrics, insights, YouTube daily, Instagram combined."""

from __future__ import annotations

from typing import Literal

from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError, cache_get, cache_set
from zernio_mcp.tools._common import client, error

_ORIGIN_MAP = {"all": "all", "via_zernio": "late", "imported": "imported"}


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def analytics_posts(
    post_id: str | None = None,
    platform: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = 10,
) -> dict:
    """Get per-post engagement metrics (likes, comments, shares, impressions).

    Without post_id: returns paginated list sorted by engagement.
    With post_id: returns engagement timeline for that specific post
    (time-series data showing how engagement changed over time).
    """
    try:
        if post_id:
            return await client().get("/v1/analytics/post-timeline", postId=post_id)
        return await client().get(
            "/v1/analytics", platform=platform,
            fromDate=from_date, toDate=to_date, limit=min(limit, 50),
        )
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def analytics_insights(
    type: Literal["best_time", "content_decay", "daily_metrics", "posting_frequency"],
    platform: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    origin: Literal["all", "via_zernio", "imported"] = "all",
) -> dict:
    """Get aggregated analytics insights.

    Use best_time when asked "when should I post?"
    Use content_decay when asked "how long do my posts stay relevant?"
    Use daily_metrics for "how are my posts doing?" overviews.
    Use posting_frequency when asked "am I posting enough?"
    """
    endpoint_map = {
        "best_time": "/v1/analytics/best-time",
        "content_decay": "/v1/analytics/content-decay",
        "daily_metrics": "/v1/analytics/daily-metrics",
        "posting_frequency": "/v1/analytics/posting-frequency",
    }
    try:
        return await client().get(
            endpoint_map[type], platform=platform,
            fromDate=from_date, toDate=to_date,
            source=_ORIGIN_MAP.get(origin, "all"),
        )
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def analytics_youtube_daily(
    account_id: str,
    from_date: str | None = None,
    to_date: str | None = None,
) -> dict:
    """Get YouTube daily view statistics.

    Args:
        account_id: YouTube account ID.
        from_date: Start of date range (ISO 8601).
        to_date: End of date range (ISO 8601).
    """
    try:
        return await client().get(
            "/v1/analytics/youtube/daily-views",
            accountId=account_id, fromDate=from_date, toDate=to_date,
        )
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def analytics_instagram(
    account_id: str,
    include_demographics: bool = True,
    from_date: str | None = None,
    to_date: str | None = None,
) -> dict:
    """Get Instagram account performance and audience demographics.

    Returns reach, impressions, profile views, follower growth.
    When include_demographics=True (default), also returns age ranges,
    gender distribution, and top locations.

    Args:
        account_id: Instagram account ID.
        include_demographics: Include audience demographics (default True).
        from_date: Start of date range (ISO 8601).
        to_date: End of date range (ISO 8601).
    """
    try:
        insights = await client().get(
            "/v1/analytics/instagram/account-insights",
            accountId=account_id, fromDate=from_date, toDate=to_date,
        )
        if include_demographics:
            cache_key = f"ig_demo_{account_id}"
            demo = cache_get(cache_key)
            if not demo:
                demo = await client().get(
                    "/v1/analytics/instagram/demographics",
                    accountId=account_id,
                )
                cache_set(cache_key, demo, ttl=300.0)
            insights["demographics"] = demo
        return insights
    except ZernioAPIError as e:
        return error(e.message)
