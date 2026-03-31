"""Queue tools: preview, create/list/update/delete slots, next slot."""

from __future__ import annotations

from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError, cache_get, cache_set, cache_invalidate_prefix
from zernio_mcp.tools._common import client, error


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def queue_preview(profile_id: str, limit: int = 5) -> dict:
    """Preview upcoming queue slots for scheduling context.

    Returns slots with datetime (ISO 8601), platform, and occupied status.
    Present max 3 suggested open slots before asking the user to choose.
    """
    try:
        return await client().get("/v1/queue/preview", profileId=profile_id, limit=limit)
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
async def queue_create_slot(
    profile_id: str,
    name: str,
    day: str,
    time: str,
    platform: str,
) -> dict:
    """Create a recurring queue time slot.

    Args:
        profile_id: The profile this slot belongs to.
        name: Name for the slot (e.g., "Morning Twitter Post").
        day: Day of week (e.g., "monday", "tuesday").
        time: Time in HH:MM format (e.g., "09:00", "14:30").
        platform: Target platform (e.g., "twitter", "instagram").
    """
    try:
        result = await client().post("/v1/queue/slots", {
            "profileId": profile_id, "name": name, "day": day, "time": time, "platform": platform,
        })
        cache_invalidate_prefix("queue_")
        return result
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def queue_list_slots(profile_id: str | None = None) -> dict:
    """List all configured recurring queue slots.

    Args:
        profile_id: Optional. Filter slots by profile.
    """
    cache_key = f"queue_slots_{profile_id or 'all'}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    try:
        result = await client().get("/v1/queue/slots", profileId=profile_id)
        cache_set(cache_key, result)
        return result
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def queue_update_slot(slot_id: str, day: str | None = None, time: str | None = None, platform: str | None = None) -> dict:
    """Update an existing queue slot.

    Args:
        slot_id: The slot to update.
        day: New day of week.
        time: New time (HH:MM).
        platform: New platform.
    """
    try:
        body: dict = {}
        if day is not None:
            body["day"] = day
        if time is not None:
            body["time"] = time
        if platform is not None:
            body["platform"] = platform
        result = await client().put("/v1/queue/slots", {"slotId": slot_id, **body})
        cache_invalidate_prefix("queue_")
        return result
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def queue_delete_slot(slot_id: str) -> dict:
    """Delete a recurring queue slot.

    Args:
        slot_id: The slot to remove.
    """
    try:
        result = await client().delete(f"/v1/queue/slots/{slot_id}")
        cache_invalidate_prefix("queue_")
        return result
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def queue_next_slot(profile_id: str) -> dict:
    """Get the next available open queue slot.

    Returns the next unoccupied slot with datetime, platform, and slot_id.

    Args:
        profile_id: The profile to check.
    """
    cache_key = f"queue_next_{profile_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    try:
        result = await client().get("/v1/queue/next-slot", profileId=profile_id)
        cache_set(cache_key, result)
        return result
    except ZernioAPIError as e:
        return error(e.message)
