"""Webhook tools: CRUD, test, and logs."""

from __future__ import annotations

from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError, validate_url_for_ssrf, SSRFError
from zernio_mcp.tools._common import client, error


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def webhooks_get() -> dict:
    """Get current webhook configuration (URL, events, status)."""
    try:
        return await client().get("/v1/webhooks/settings")
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
async def webhooks_create(url: str, events: list[str]) -> dict:
    """Create a webhook configuration.

    Args:
        url: Webhook endpoint URL (HTTPS only, no private IPs).
        events: List of event types to subscribe to.
    """
    try:
        await validate_url_for_ssrf(url)
        return await client().post("/v1/webhooks/settings", {"url": url, "events": events})
    except SSRFError as e:
        return error(str(e))
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def webhooks_update(url: str | None = None, events: list[str] | None = None) -> dict:
    """Update webhook configuration.

    Args:
        url: New webhook URL (HTTPS only, no private IPs).
        events: Updated event types.
    """
    try:
        if url is not None:
            await validate_url_for_ssrf(url)
        body: dict = {}
        if url is not None:
            body["url"] = url
        if events is not None:
            body["events"] = events
        return await client().put("/v1/webhooks/settings", body)
    except SSRFError as e:
        return error(str(e))
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def webhooks_delete() -> dict:
    """Remove webhook configuration."""
    try:
        return await client().delete("/v1/webhooks/settings")
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
async def webhooks_test() -> dict:
    """Send a test event to the configured webhook URL."""
    try:
        return await client().post("/v1/webhooks/test")
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def webhooks_logs(limit: int = 20) -> dict:
    """Get webhook delivery logs with status codes and timestamps.

    Args:
        limit: Max results (default 20).
    """
    try:
        return await client().get("/v1/webhooks/logs", limit=limit)
    except ZernioAPIError as e:
        return error(e.message)
