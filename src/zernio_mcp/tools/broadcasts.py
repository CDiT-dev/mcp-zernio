"""Broadcast tools: campaign CRUD."""

from __future__ import annotations

from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError
from zernio_mcp.tools._common import client, error


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def broadcasts_list(limit: int = 20) -> dict:
    """[social] List broadcast campaigns.

    Args:
        limit: Max results (default 20).
    """
    try:
        return await client().get("/v1/broadcasts", limit=limit)
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
async def broadcasts_create(name: str, content: str, account_ids: list[str]) -> dict:
    """[social] Create a broadcast campaign.

    Args:
        name: Campaign name.
        content: Broadcast message content.
        account_ids: Target account IDs.
    """
    try:
        return await client().post("/v1/broadcasts", {
            "name": name, "content": content, "accountIds": account_ids,
        })
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def broadcasts_get(broadcast_id: str) -> dict:
    """[social] Get broadcast campaign details including status and metrics.

    Args:
        broadcast_id: The broadcast to retrieve.
    """
    try:
        return await client().get(f"/v1/broadcasts/{broadcast_id}")
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def broadcasts_update(broadcast_id: str, name: str | None = None, content: str | None = None) -> dict:
    """[social] Update a broadcast campaign.

    Args:
        broadcast_id: The broadcast to update.
        name: New campaign name.
        content: New message content.
    """
    try:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if content is not None:
            body["content"] = content
        return await client().put(f"/v1/broadcasts/{broadcast_id}", body)
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def broadcasts_delete(broadcast_id: str) -> dict:
    """[social] Delete a broadcast campaign.

    Args:
        broadcast_id: The broadcast to delete.
    """
    try:
        return await client().delete(f"/v1/broadcasts/{broadcast_id}")
    except ZernioAPIError as e:
        return error(e.message)
