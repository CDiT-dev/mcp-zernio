"""Contact CRM tools: list, create, get, update, delete."""

from __future__ import annotations

from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError, cache_get, cache_set, cache_invalidate_prefix
from zernio_mcp.tools._common import client, error


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def contacts_list(query: str | None = None, limit: int = 20) -> dict:
    """[social] List contacts. Optionally search by name or identifier.

    Args:
        query: Optional search query.
        limit: Max results (default 20).
    """
    cache_key = f"contacts_{query or 'all'}_{limit}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    try:
        result = await client().get("/v1/contacts", query=query, limit=limit)
        cache_set(cache_key, result)
        return result
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
async def contacts_create(
    name: str,
    email: str | None = None,
    phone: str | None = None,
    platform: str | None = None,
    platform_user_id: str | None = None,
) -> dict:
    """[social] Create a contact.

    Args:
        name: Contact name.
        email: Optional email address.
        phone: Optional phone number.
        platform: Optional platform name.
        platform_user_id: Optional platform-specific user ID.
    """
    try:
        body: dict = {"name": name}
        if email:
            body["email"] = email
        if phone:
            body["phone"] = phone
        if platform:
            body["platform"] = platform
        if platform_user_id:
            body["platformUserId"] = platform_user_id
        result = await client().post("/v1/contacts", body)
        cache_invalidate_prefix("contacts_")
        return result
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def contacts_get(contact_id: str) -> dict:
    """[social] Get contact details.

    Args:
        contact_id: The contact to retrieve.
    """
    try:
        return await client().get(f"/v1/contacts/{contact_id}")
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def contacts_update(
    contact_id: str,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
) -> dict:
    """[social] Update a contact.

    Args:
        contact_id: The contact to update.
        name: New name.
        email: New email.
        phone: New phone.
    """
    try:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if email is not None:
            body["email"] = email
        if phone is not None:
            body["phone"] = phone
        return await client().put(f"/v1/contacts/{contact_id}", body)
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def contacts_delete(contact_id: str) -> dict:
    """[social] Delete a contact.

    Args:
        contact_id: The contact to delete.
    """
    try:
        result = await client().delete(f"/v1/contacts/{contact_id}")
        cache_invalidate_prefix("contacts_")
        return result
    except ZernioAPIError as e:
        return error(e.message)
