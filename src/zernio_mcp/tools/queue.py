"""Queue tools: preview, create/list/update/delete slots, next slot."""

from __future__ import annotations

from typing import Any, Literal

from fastmcp import Context
from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError, cache_get, cache_set, cache_invalidate_prefix
from zernio_mcp.models import QueueSlotList
from zernio_mcp.tools._common import client, error

_DAY_MAP = {
    "monday": 1, "tuesday": 2, "wednesday": 3, "thursday": 4,
    "friday": 5, "saturday": 6, "sunday": 0,
}


def _extract_slots(payload: Any) -> list[dict]:
    """Normalize the various shapes the Zernio queue endpoints return.

    Handles ``{"slots": [...]}``, ``{"schedules": [...]}``, ``{"data": [...]}``,
    plain lists, and the legacy single-schedule envelope that returned just the
    default schedule (see CDI-1058).
    """
    if payload is None:
        return []
    if isinstance(payload, list):
        return [s for s in payload if isinstance(s, dict)]
    if isinstance(payload, dict):
        for key in ("slots", "schedules", "queues", "data", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [s for s in value if isinstance(s, dict)]
        # Legacy: a single-schedule envelope (``{"schedule": {...}}`` /
        # ``{"slot": {...}}``) — wrap it so callers always see a list.
        for key in ("schedule", "slot"):
            value = payload.get(key)
            if isinstance(value, dict):
                return [value]
    return []


@mcp.tool(
    title="Preview upcoming queue slots",
    tags={"social", "queue", "read"},
    output_schema=QueueSlotList.model_json_schema(),
    annotations=ToolAnnotations(
        title="Preview upcoming queue slots",
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def queue_preview(profile_id: str, limit: int = 5) -> dict:
    """[social] Preview upcoming queue slots for scheduling context.

    Returns slots with datetime (ISO 8601), platform, and occupied status.
    Present max 3 suggested open slots before asking the user to choose.
    """
    try:
        return await client().get("/v1/queue/preview", profileId=profile_id, limit=limit)
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(
    title="Create recurring queue slot",
    tags={"social", "queue", "write"},
    annotations=ToolAnnotations(
        title="Create recurring queue slot",
        readOnlyHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def queue_create_slot(
    profile_id: str,
    name: str,
    day: Literal["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
    time: str,
    platform: str,
    timezone: str = "Europe/Berlin",
) -> dict:
    """[social] Create a recurring queue time slot.

    ## Name uniqueness (CDI-1060)

    The Zernio API enforces unique slot names *per profile*. Calling this with a
    ``name`` that already exists on the same ``profile_id`` returns
    ``400 'A queue with this name already exists for this profile'``. Use a
    naming convention like ``"{Profile} {Day} — {Platform} {Time}"`` to avoid
    collisions, or call ``queue_list_slots`` first to see existing names.

    ## Supported platforms (CDI-1063)

    Pass platform identifiers such as ``twitter``, ``bluesky``, ``linkedin``,
    ``facebook``, ``instagram``, ``threads``, ``tiktok``, ``youtube``,
    ``pinterest``, ``reddit``. The slot fires for the account on this profile
    that matches ``platform``; if multiple accounts on this profile share the
    same platform, you must split them across profiles or rely on the platform
    selecting the first matching account.

    Args:
        profile_id: The profile this slot belongs to.
        name: Name for the slot (e.g., "Morning Twitter Post"). Must be unique per profile.
        day: Day of week (e.g., "monday", "tuesday").
        time: Time in HH:MM format (e.g., "09:00", "14:30").
        platform: Target platform (e.g., "twitter", "instagram").
        timezone: IANA timezone (e.g., "Europe/Berlin", "America/New_York"). Defaults to Europe/Berlin.
    """
    day_num = _DAY_MAP.get(day.lower())
    if day_num is None:
        return error(f"Invalid day '{day}'. Use: monday, tuesday, wednesday, thursday, friday, saturday, sunday")
    try:
        result = await client().post("/v1/queue/slots", {
            "profileId": profile_id,
            "name": name,
            "timezone": timezone,
            "slots": [{"dayOfWeek": day_num, "time": time, "platform": platform}],
        })
        cache_invalidate_prefix("queue_")
        return result
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(
    title="List queue slots",
    tags={"social", "queue", "read"},
    output_schema=QueueSlotList.model_json_schema(),
    annotations=ToolAnnotations(
        title="List queue slots",
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def queue_list_slots(profile_id: str | None = None) -> dict:
    """[social] List all configured recurring queue slots / schedules.

    Returns ``{"slots": [...]}`` containing every schedule for the requested
    profile (or every profile if ``profile_id`` is omitted), with the
    ``isDefault`` flag preserved on each entry. Callers can filter to the
    default schedule client-side.

    Fixes CDI-1058: earlier versions only ever returned the schedule marked
    ``isDefault: true``. We now request ``includeAll=true`` and additionally
    fall back to enumerating profiles when the upstream still returns only the
    default for a profile-scoped call.

    Args:
        profile_id: Optional. Filter slots by profile.
    """
    cache_key = f"queue_slots_{profile_id or 'all'}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    try:
        # Ask upstream for every schedule. Newer Zernio backends honour
        # ``includeAll`` / ``all`` and return every schedule; older ones ignore
        # the flag and still return just the default. Either way, the call is
        # safe.
        raw = await client().get(
            "/v1/queue/slots",
            profileId=profile_id,
            includeAll="true",
            all="true",
        )
        slots = _extract_slots(raw)

        # Fallback: if we only got the default schedule back and a profile was
        # requested, retry through the profile-scoped collection endpoint.
        if profile_id and len(slots) <= 1:
            try:
                fallback = await client().get(
                    f"/v1/profiles/{profile_id}/queue/slots", includeAll="true"
                )
                fallback_slots = _extract_slots(fallback)
                if len(fallback_slots) > len(slots):
                    slots = fallback_slots
            except ZernioAPIError:
                # Endpoint may not exist on older deployments — keep the
                # primary result silently.
                pass

        result = {"slots": slots}
        cache_set(cache_key, result)
        return result
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(
    title="Update queue slot",
    tags={"social", "queue", "write"},
    annotations=ToolAnnotations(
        title="Update queue slot",
        readOnlyHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def queue_update_slot(slot_id: str, day: str | None = None, time: str | None = None, platform: str | None = None) -> dict:
    """[social] Update an existing queue slot.

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
        result = await client().put(f"/v1/queue/slots/{slot_id}", body)
        cache_invalidate_prefix("queue_")
        return result
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(
    title="Delete queue slot",
    tags={"social", "queue", "write", "destructive"},
    annotations=ToolAnnotations(
        title="Delete queue slot",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def queue_delete_slot(slot_id: str) -> dict:
    """[social] Delete a recurring queue slot.

    ## Known constraints

    * The Zernio backend refuses to delete the *default* schedule for a
      profile. If you need to remove it, demote it first via the UI (promote
      another schedule to default), then call this tool. See CDI-1062.
    * Deleting non-default schedules sometimes returns a Next.js HTML 404
      page upstream (CDI-1057). The MCP layer now normalises that into a
      clean structured error instead of forwarding raw HTML.

    Args:
        slot_id: The slot to remove.
    """
    try:
        result = await client().delete(f"/v1/queue/slots/{slot_id}")
        cache_invalidate_prefix("queue_")
        return result
    except ZernioAPIError as e:
        # CDI-1057 / CDI-1062: surface actionable, structured errors instead
        # of leaking raw upstream HTML or generic 404s.
        if e.status_code == 404:
            return {
                "error": (
                    f"Queue slot {slot_id} could not be deleted via the API. "
                    "Common causes: the slot doesn't exist, or it is the "
                    "profile's default schedule (which the backend protects "
                    "from deletion — demote it in the Zernio UI first)."
                ),
                "status_code": 404,
                "slot_id": slot_id,
            }
        if e.status_code in (400, 409, 422) and (
            "default" in e.message.lower() or "cannot be deleted" in e.message.lower()
        ):
            return {
                "error": (
                    f"Queue slot {slot_id} is the default schedule for its "
                    "profile and cannot be deleted directly. Promote another "
                    "schedule to default in the Zernio UI first, then retry."
                ),
                "status_code": e.status_code,
                "slot_id": slot_id,
            }
        return error(e.message)


@mcp.tool(
    title="Next open queue slot",
    tags={"social", "queue", "read"},
    annotations=ToolAnnotations(
        title="Next open queue slot",
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def queue_next_slot(profile_id: str) -> dict:
    """[social] Get the next available open queue slot.

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


# ── CDI-1059: bulk and reset primitives ─────────────────────────


def _slot_is_default(slot: dict) -> bool:
    """Best-effort check for whether a returned schedule is the default."""
    for key in ("isDefault", "is_default", "default"):
        val = slot.get(key)
        if isinstance(val, bool):
            return val
    return False


def _slot_identifier(slot: dict) -> str | None:
    for key in ("_id", "id", "slotId", "scheduleId"):
        val = slot.get(key)
        if isinstance(val, str) and val:
            return val
    return None


@mcp.tool(
    title="Clear all queue slots for a profile",
    tags={"social", "queue", "write", "bulk", "destructive"},
    annotations=ToolAnnotations(
        title="Clear all queue slots for a profile",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def queue_clear(
    profile_id: str,
    include_default: bool = False,
    ctx: Context | None = None,
) -> dict:
    """[social] Remove every recurring queue slot for a profile.

    Iterates over every schedule returned by ``queue_list_slots(profile_id)``
    and calls ``queue_delete_slot`` on each. By default the profile's *default*
    schedule is preserved because the Zernio backend refuses to delete it
    (see CDI-1062); set ``include_default=True`` to attempt deletion anyway —
    the call will be reported as ``skipped_default`` if the backend rejects it.

    Returns ``{"deleted": [...], "failed": [...], "skipped_default": [...]}``.

    Args:
        profile_id: Profile whose schedules to remove.
        include_default: Attempt to delete the default schedule too.
        ctx: Injected by FastMCP for progress/log reporting. Optional; callers
            never pass it.
    """
    listing = await queue_list_slots(profile_id=profile_id)
    if "error" in listing:
        return listing

    deleted: list[str] = []
    failed: list[dict] = []
    skipped_default: list[str] = []

    slots = listing.get("slots", [])
    total = len(slots)
    if ctx and total:
        await ctx.info(f"Clearing {total} queue slot(s) for profile {profile_id}.")
    for idx, slot in enumerate(slots):
        if ctx:
            await ctx.report_progress(idx, total, "Deleting queue slots")
        slot_id = _slot_identifier(slot)
        if not slot_id:
            continue
        if _slot_is_default(slot) and not include_default:
            skipped_default.append(slot_id)
            continue
        try:
            await client().delete(f"/v1/queue/slots/{slot_id}")
            deleted.append(slot_id)
        except ZernioAPIError as exc:
            entry = {"slot_id": slot_id, "status_code": exc.status_code, "message": exc.message}
            if _slot_is_default(slot):
                skipped_default.append(slot_id)
            else:
                failed.append(entry)

    cache_invalidate_prefix("queue_")
    if ctx and total:
        await ctx.report_progress(total, total, "Queue cleared")
    return {
        "deleted": deleted,
        "failed": failed,
        "skipped_default": skipped_default,
    }


@mcp.tool(
    title="Apply a full queue schedule",
    tags={"social", "queue", "write", "bulk"},
    annotations=ToolAnnotations(
        title="Apply a full queue schedule",
        readOnlyHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def queue_set_schedule(
    profile_id: str,
    slots: list[dict],
    timezone: str = "Europe/Berlin",
    replace: bool = True,
    ctx: Context | None = None,
) -> dict:
    """[social] Apply a queue schedule from a spec — optionally wiping existing slots first.

    Each entry in ``slots`` is a dict with keys:
      * ``day`` — one of monday..sunday
      * ``time`` — HH:MM
      * ``platform`` — e.g. twitter, linkedin
      * ``name`` (optional) — slot name; defaults to
        ``"{Day} {Platform} {Time}"`` if omitted. Names must be unique per
        profile (CDI-1060).

    When ``replace=True`` (default) the tool first attempts to clear the
    existing queue via ``queue_clear`` — preserving the default schedule that
    Zernio refuses to delete (CDI-1062). When ``replace=False`` the new slots
    are added without touching existing ones.

    Returns ``{"created": [...], "failed": [...], "cleared": {...}}``. If any
    slot creation fails the already-created slots are rolled back before the
    error is returned.

    Args:
        profile_id: The profile to apply the schedule to.
        slots: List of slot specs.
        timezone: IANA timezone for every slot in this batch.
        replace: When True, clear existing slots before applying.
        ctx: Injected by FastMCP for progress/log reporting. Optional; callers
            never pass it.
    """
    if not slots:
        return error("queue_set_schedule requires a non-empty 'slots' list.")

    # Validate the spec up front so we don't half-apply on bad input.
    normalised: list[dict] = []
    for idx, spec in enumerate(slots):
        if not isinstance(spec, dict):
            return error(f"slots[{idx}] must be an object with day/time/platform.")
        day = (spec.get("day") or "").lower()
        time_str = spec.get("time")
        platform = spec.get("platform")
        name = spec.get("name")
        if day not in _DAY_MAP:
            return error(
                f"slots[{idx}].day = {spec.get('day')!r} — must be one of "
                "monday, tuesday, wednesday, thursday, friday, saturday, sunday."
            )
        if not isinstance(time_str, str) or not time_str:
            return error(f"slots[{idx}].time must be a non-empty HH:MM string.")
        if not isinstance(platform, str) or not platform:
            return error(f"slots[{idx}].platform must be a non-empty string.")
        normalised.append({
            "day": day,
            "time": time_str,
            "platform": platform,
            "name": name or f"{day.capitalize()} {platform} {time_str}",
        })

    cleared_summary: dict | None = None
    if replace:
        cleared_summary = await queue_clear(
            profile_id=profile_id, include_default=False, ctx=ctx
        )
        if "error" in cleared_summary:
            return cleared_summary

    created: list[dict] = []
    total = len(normalised)
    if ctx:
        await ctx.info(f"Creating {total} queue slot(s) for profile {profile_id}.")
    try:
        for idx, spec in enumerate(normalised):
            if ctx:
                await ctx.report_progress(idx, total, "Creating queue slots")
            day_num = _DAY_MAP[spec["day"]]
            result = await client().post("/v1/queue/slots", {
                "profileId": profile_id,
                "name": spec["name"],
                "timezone": timezone,
                "slots": [{
                    "dayOfWeek": day_num,
                    "time": spec["time"],
                    "platform": spec["platform"],
                }],
            })
            slot_id = (
                result.get("slot", {}).get("_id")
                or result.get("slot", {}).get("id")
                or result.get("_id")
                or result.get("id")
            )
            created.append({"slot_id": slot_id, "name": spec["name"], "result": result})
    except ZernioAPIError as exc:
        # Rollback: best-effort delete of every slot we created in this run.
        rollback_failures: list[dict] = []
        for entry in created:
            sid = entry.get("slot_id")
            if not sid:
                continue
            try:
                await client().delete(f"/v1/queue/slots/{sid}")
            except ZernioAPIError as rb_exc:
                rollback_failures.append({
                    "slot_id": sid,
                    "status_code": rb_exc.status_code,
                    "message": rb_exc.message,
                })
        cache_invalidate_prefix("queue_")
        return {
            "error": f"queue_set_schedule failed mid-flight: {exc.message}",
            "status_code": exc.status_code,
            "rolled_back": [c.get("slot_id") for c in created if c.get("slot_id")],
            "rollback_failures": rollback_failures,
            "cleared": cleared_summary,
        }

    cache_invalidate_prefix("queue_")
    if ctx:
        await ctx.report_progress(total, total, "Schedule applied")
    return {
        "created": created,
        "cleared": cleared_summary,
    }


__all__ = [
    "queue_preview",
    "queue_create_slot",
    "queue_list_slots",
    "queue_update_slot",
    "queue_delete_slot",
    "queue_next_slot",
    "queue_clear",
    "queue_set_schedule",
]
