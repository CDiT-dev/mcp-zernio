"""Account tools: list, health, update, delete, follower stats."""

from __future__ import annotations

from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import (
    ZernioAPIError, cache_get, cache_set, cache_invalidate, strip_pii,
)
from zernio_mcp.tools._common import client, error


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def accounts_list() -> dict:
    """List all connected social media accounts.

    Returns each account's id, platform, username, displayName, and profileName.
    Use this to find account IDs before calling posts_create.
    """
    cached = cache_get("accounts_list")
    if cached:
        return cached
    try:
        data = await client().get("/v1/accounts")
        accounts = data.get("accounts", data if isinstance(data, list) else [])
        result = {"accounts": [strip_pii(a) for a in accounts]}
        cache_set("accounts_list", result)
        return result
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def accounts_health(account_id: str | None = None) -> dict:
    """Check token health and expiry status for connected accounts.

    Without account_id: returns status for all accounts.
    With account_id: returns detailed health for that specific account only.

    When a token is expired, includes reauth instructions directing the user
    to app.zernio.com/accounts to reconnect.
    """
    try:
        if account_id:
            data = await client().get(f"/v1/accounts/{account_id}/health")
        else:
            data = await client().get("/v1/accounts/health")
        accounts = data.get("accounts", [data] if isinstance(data, dict) and "status" in data else data if isinstance(data, list) else [])
        results = []
        for a in (accounts if isinstance(accounts, list) else [accounts]):
            entry = strip_pii(a)
            if entry.get("status") in ("expired", "revoked", "error"):
                entry["reauth_instructions"] = (
                    "Your connection needs to be renewed. "
                    "Go to https://app.zernio.com/accounts to reconnect this account."
                )
            results.append(entry)
        return {"accounts": results}
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def accounts_update(account_id: str, settings: dict) -> dict:
    """Update account settings.

    Args:
        account_id: The account to update.
        settings: Dictionary of settings to update.
    """
    try:
        result = await client().put(f"/v1/accounts/{account_id}", settings)
        cache_invalidate("accounts_list")
        return result
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def accounts_delete(account_id: str) -> dict:
    """Disconnect a social media account from Zernio.

    This removes the OAuth connection. The account's posts remain on the platform.

    Args:
        account_id: The account to disconnect.
    """
    try:
        result = await client().delete(f"/v1/accounts/{account_id}")
        cache_invalidate("accounts_list")
        return result
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def accounts_follower_stats() -> dict:
    """Get follower count trends over time for all connected accounts.

    Returns per-account follower counts over time. Use this when asked
    "am I growing?" or "how are my followers doing?"
    """
    cached = cache_get("accounts_follower_stats")
    if cached:
        return cached
    try:
        result = await client().get("/v1/accounts/follower-stats")
        cache_set("accounts_follower_stats", result)
        return result
    except ZernioAPIError as e:
        return error(e.message)
