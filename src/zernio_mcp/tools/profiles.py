"""Profile tools: list, create, get, update, delete."""

from __future__ import annotations

from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError, cache_get, cache_set, cache_invalidate
from zernio_mcp.tools._common import client, error


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def profiles_list() -> dict:
    """List all brand profile groupings with their associated account IDs.

    A profile is a brand grouping containing one or more connected accounts.
    Use profiles_list to identify which accounts belong to a brand, then pass
    account_ids from the profile to posts_create.
    """
    cached = cache_get("profiles_list")
    if cached:
        return cached
    try:
        result = await client().get("/v1/profiles")
        cache_set("profiles_list", result)
        return result
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
async def profiles_create(name: str) -> dict:
    """Create a new brand profile.

    Args:
        name: Name for the new profile (e.g., "CDIT Brand").
    """
    try:
        result = await client().post("/v1/profiles", {"name": name})
        cache_invalidate("profiles_list")
        return result
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def profiles_get(profile_id: str) -> dict:
    """Get details for a specific brand profile.

    Args:
        profile_id: The profile to retrieve.
    """
    try:
        return await client().get(f"/v1/profiles/{profile_id}")
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def profiles_update(profile_id: str, name: str) -> dict:
    """Update a brand profile.

    Args:
        profile_id: The profile to update.
        name: New name for the profile.
    """
    try:
        result = await client().put(f"/v1/profiles/{profile_id}", {"name": name})
        cache_invalidate("profiles_list")
        return result
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def profiles_delete(profile_id: str) -> dict:
    """Delete a brand profile. Connected accounts are not disconnected.

    Args:
        profile_id: The profile to delete.
    """
    try:
        result = await client().delete(f"/v1/profiles/{profile_id}")
        cache_invalidate("profiles_list")
        return result
    except ZernioAPIError as e:
        return error(e.message)
