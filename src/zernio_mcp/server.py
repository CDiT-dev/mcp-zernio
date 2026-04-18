"""MCP server for Zernio social media management — ~83 tools across P0-P3."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastmcp import FastMCP
from mcp.types import Icon
from starlette.requests import Request
from starlette.responses import JSONResponse

from . import __version__
from .auth import BearerTokenVerifier
from zernio_mcp.client import close_shared_client, get_shared_client
from zernio_mcp.config import settings


@asynccontextmanager
async def lifespan(server):
    get_shared_client()  # warm up connection pool
    yield
    await close_shared_client()


_api_key = os.getenv("MCP_API_KEY", "")
if settings.mcp_transport == "http" and not _api_key:
    raise SystemExit(
        "MCP_API_KEY is required in HTTP mode. Refusing to start "
        "an unauthenticated server."
    )
_auth = BearerTokenVerifier(api_key=_api_key) if _api_key else None
_start_time = datetime.now(timezone.utc)

mcp = FastMCP(
    "mcp-zernio",
    auth=_auth,
    lifespan=lifespan,
    icons=[
        Icon(
            src="https://zernio.com/icon.svg?v=3",
            mimeType="image/svg+xml",
        ),
    ],
)


def _register_tools():
    """Import all tool modules to register them with the mcp instance."""
    import zernio_mcp.tools  # noqa: F401


_register_tools()


# ---------------------------------------------------------------------------
# Custom HTTP routes: browser-based media upload
# ---------------------------------------------------------------------------

from zernio_mcp.upload import register_upload_routes  # noqa: E402

register_upload_routes(mcp)

from zernio_mcp.inbox import register_inbox_routes  # noqa: E402

register_inbox_routes(mcp)


@mcp.custom_route("/health", methods=["GET"])
async def _health(request: Request) -> JSONResponse:
    return JSONResponse({
        "status": "healthy",
        "service": "mcp-zernio",
        "version": __version__,
        "upstream_reachable": True,
        "uptime_seconds": int((datetime.now(timezone.utc) - _start_time).total_seconds()),
    })


@mcp.custom_route("/healthz", methods=["GET"])
async def _healthz(request: Request) -> JSONResponse:
    return await _health(request)


def main() -> None:
    if settings.mcp_transport == "http":
        mcp.run(
            transport="streamable-http",
            host=settings.host,
            port=settings.port,
            stateless_http=True,
        )
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
