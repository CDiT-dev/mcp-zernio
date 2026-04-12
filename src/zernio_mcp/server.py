"""MCP server for Zernio social media management — ~83 tools across P0-P3."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastmcp import FastMCP
from mcp.types import Icon

from .auth import BearerTokenVerifier
from zernio_mcp.client import close_shared_client, get_shared_client
from zernio_mcp.config import settings


@asynccontextmanager
async def lifespan(server):
    get_shared_client()  # warm up connection pool
    yield
    await close_shared_client()


_api_key = os.getenv("MCP_API_KEY", "")
_auth = BearerTokenVerifier(api_key=_api_key) if _api_key else None

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


def main() -> None:
    if settings.mcp_transport == "http":
        mcp.run(transport="streamable-http", host=settings.host, port=settings.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
