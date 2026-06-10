"""Webhook tools: CRUD, test, and logs."""

from __future__ import annotations

from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError, validate_url_for_ssrf, SSRFError
from zernio_mcp.tools._common import client, error


@mcp.tool(
    title="Webhooks get",
    tags={"social", "webhooks", "read"},
    annotations=ToolAnnotations(title="Webhooks get", readOnlyHint=True, idempotentHint=True, openWorldHint=True),
)
async def webhooks_get() -> dict:
    """[social] Get current webhook configuration (URL, events, status)."""
    try:
        return await client().get("/v1/webhooks/settings")
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(
    title="Webhooks create",
    tags={"social", "webhooks", "write"},
    annotations=ToolAnnotations(title="Webhooks create", readOnlyHint=False, idempotentHint=False, openWorldHint=True),
)
async def webhooks_create(url: str, events: list[str]) -> dict:
    """[social] Create a webhook configuration.

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


@mcp.tool(
    title="Webhooks update",
    tags={"social", "webhooks", "write"},
    annotations=ToolAnnotations(title="Webhooks update", readOnlyHint=False, idempotentHint=True, openWorldHint=True),
)
async def webhooks_update(url: str | None = None, events: list[str] | None = None) -> dict:
    """[social] Update webhook configuration.

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


@mcp.tool(
    title="Webhooks delete",
    tags={"social", "webhooks", "write", "destructive"},
    annotations=ToolAnnotations(title="Webhooks delete", readOnlyHint=False, destructiveHint=True, idempotentHint=True, openWorldHint=True),
)
async def webhooks_delete() -> dict:
    """[social] Remove webhook configuration."""
    try:
        return await client().delete("/v1/webhooks/settings")
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(
    title="Webhooks test",
    tags={"social", "webhooks", "write"},
    annotations=ToolAnnotations(title="Webhooks test", readOnlyHint=False, idempotentHint=False, openWorldHint=True),
)
async def webhooks_test() -> dict:
    """[social] Send a test event to the configured webhook URL."""
    try:
        return await client().post("/v1/webhooks/test")
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(
    title="Webhooks logs",
    tags={"social", "webhooks", "read"},
    annotations=ToolAnnotations(title="Webhooks logs", readOnlyHint=True, idempotentHint=True, openWorldHint=True),
)
async def webhooks_logs(limit: int = 20) -> dict:
    """[social] Get webhook delivery logs with status codes and timestamps.

    Args:
        limit: Max results (default 20).
    """
    try:
        return await client().get("/v1/webhooks/logs", limit=limit)
    except ZernioAPIError as e:
        return error(e.message)
