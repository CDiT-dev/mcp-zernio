"""Activity log tools: post logs, per-post logs, connection logs."""

from __future__ import annotations

from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError
from zernio_mcp.models import LogList
from zernio_mcp.tools._common import client, error


@mcp.tool(
    title="Logs posts",
    tags={"social", "logs", "read"},
    output_schema=LogList.model_json_schema(),
    annotations=ToolAnnotations(title="Logs posts", readOnlyHint=True, idempotentHint=True, openWorldHint=True),
)
async def logs_posts(limit: int = 20) -> dict:
    """[social] Get post activity logs (created, published, failed, deleted events).

    Args:
        limit: Max results (default 20).
    """
    try:
        return await client().get("/v1/posts/logs", limit=limit)
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(
    title="Logs post detail",
    tags={"social", "logs", "read"},
    annotations=ToolAnnotations(title="Logs post detail", readOnlyHint=True, idempotentHint=True, openWorldHint=True),
)
async def logs_post_detail(post_id: str) -> dict:
    """[social] Get the full event history for a specific post.

    Args:
        post_id: The post to get logs for.
    """
    try:
        return await client().get(f"/v1/posts/{post_id}/logs")
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(
    title="Logs connections",
    tags={"social", "logs", "read"},
    annotations=ToolAnnotations(title="Logs connections", readOnlyHint=True, idempotentHint=True, openWorldHint=True),
)
async def logs_connections() -> dict:
    """[social] Get account connection and disconnection event logs."""
    try:
        return await client().get("/v1/connections/logs")
    except ZernioAPIError as e:
        return error(e.message)
