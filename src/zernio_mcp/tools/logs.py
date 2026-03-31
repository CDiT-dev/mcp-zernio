"""Activity log tools: post logs, per-post logs, connection logs."""

from __future__ import annotations

from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError
from zernio_mcp.tools._common import client, error


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def logs_posts(limit: int = 20) -> dict:
    """Get post activity logs (created, published, failed, deleted events).

    Args:
        limit: Max results (default 20).
    """
    try:
        return await client().get("/v1/posts/logs", limit=limit)
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def logs_post_detail(post_id: str) -> dict:
    """Get the full event history for a specific post.

    Args:
        post_id: The post to get logs for.
    """
    try:
        return await client().get(f"/v1/posts/{post_id}/logs")
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def logs_connections() -> dict:
    """Get account connection and disconnection event logs."""
    try:
        return await client().get("/v1/connections/logs")
    except ZernioAPIError as e:
        return error(e.message)
