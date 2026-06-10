"""Review tools: list and reply to Google Business reviews."""

from __future__ import annotations

from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError
from zernio_mcp.tools._common import client, error


@mcp.tool(
    title="Reviews list",
    tags={"social", "reviews", "read"},
    annotations=ToolAnnotations(title="Reviews list", readOnlyHint=True, idempotentHint=True, openWorldHint=True),
)
async def reviews_list(limit: int = 20) -> dict:
    """[social] List Google Business reviews with rating, content, author, and reply status.

    Args:
        limit: Max results (default 20).
    """
    try:
        return await client().get("/v1/inbox/reviews", limit=limit)
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(
    title="Reviews reply",
    tags={"social", "reviews", "write"},
    annotations=ToolAnnotations(title="Reviews reply", readOnlyHint=False, idempotentHint=False, openWorldHint=True),
)
async def reviews_reply(review_id: str, content: str) -> dict:
    """[social] Reply to a Google Business review. This is publicly visible — confirm with user.

    Args:
        review_id: The review to reply to.
        content: Reply text.
    """
    try:
        return await client().post(f"/v1/inbox/reviews/{review_id}/reply", {"content": content})
    except ZernioAPIError as e:
        return error(e.message)
