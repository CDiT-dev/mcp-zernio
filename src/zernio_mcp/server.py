"""MCP server for Zernio social media management — ~83 tools across P0-P3."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastmcp import FastMCP

from zernio_mcp.auth import build_auth
from zernio_mcp.client import close_shared_client, get_shared_client
from zernio_mcp.config import settings


@asynccontextmanager
async def lifespan(server):
    get_shared_client()  # warm up connection pool
    yield
    await close_shared_client()


mcp = FastMCP("mcp-zernio", auth=build_auth(), lifespan=lifespan)


def _register_tools():
    """Import all tool modules to register them with the mcp instance."""
    import zernio_mcp.tools  # noqa: F401


_register_tools()


def main() -> None:
    if settings.mcp_transport == "http":
        mcp.run(transport="streamable-http", host=settings.host, port=settings.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
