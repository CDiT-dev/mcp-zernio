"""Misc tools: usage stats, account groups."""

from __future__ import annotations

from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError
from zernio_mcp.tools._common import client, error


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def usage_stats() -> dict:
    """Get API usage counts, post counts, and billing information."""
    try:
        return await client().get("/v1/usage-stats")
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def account_groups_list() -> dict:
    """List account groups with member accounts."""
    try:
        return await client().get("/v1/account-groups")
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
async def account_groups_create(name: str, account_ids: list[str]) -> dict:
    """Create an account group.

    Args:
        name: Group name.
        account_ids: Account IDs to include in the group.
    """
    try:
        return await client().post("/v1/account-groups", {"name": name, "accountIds": account_ids})
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def account_groups_delete(group_id: str) -> dict:
    """Delete an account group.

    Args:
        group_id: The group to delete.
    """
    try:
        return await client().delete(f"/v1/account-groups/{group_id}")
    except ZernioAPIError as e:
        return error(e.message)
