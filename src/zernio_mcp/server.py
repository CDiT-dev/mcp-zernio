"""MCP server for Zernio social media management — ~83 tools across P0-P3."""

from __future__ import annotations

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


# Bearer token auth via settings (fail-fast for HTTP mode handled in config.py).
_api_key = settings.mcp_api_key.get_secret_value()
_auth = BearerTokenVerifier(api_key=_api_key) if _api_key else None
_start_time = datetime.now(timezone.utc)

_INSTRUCTIONS = """\
Zernio is a social media management platform. This server exposes ~90 tools for
posting, scheduling, inbox/comment management, analytics, and account/profile
administration across Twitter/X, Bluesky, LinkedIn, Facebook, Instagram,
Threads, TikTok, YouTube, Pinterest, and Reddit.

How to pick a tool:
- Almost every write needs an accountId (and often a profileId) first. Read the
  resource zernio://accounts to resolve account ids and zernio://profiles for
  brand groupings instead of spending a tool call; fall back to accounts_list /
  profiles_list. If multiple accounts match a platform, ask which brand profile.
- Before posting, read zernio://platforms for per-platform character limits and
  quirks (Instagram/TikTok require media, YouTube is video-only, Meta 'Threads'
  has no native API threading), then validate with validate_post /
  validate_post_length. Only twitter and bluesky support thread_items.
- Posts lifecycle: posts_create (draft/now/scheduled) → posts_update edits a
  draft/scheduled → posts_schedule promotes a draft to scheduled (delete-then-
  recreate; the post id CHANGES) → posts_delete removes a draft/scheduled →
  posts_unpublish removes a published post → posts_retry re-runs a failed one.
- Inbox vs CRM: social DMs/comments live here (zernio); live-chat/CRM is a
  different server. Sending DMs/replies contacts real people — confirm wording
  with the user first.

Tool annotations are accurate: readOnlyHint marks safe reads, destructiveHint
marks irreversible deletes/unpublishes, idempotentHint marks safe-to-retry
calls, and openWorldHint marks calls that hit external platforms.

Guided prompts: draft_cross_platform_campaign, triage_inbox,
weekly_analytics_review wrap the common multi-step jobs.
"""

mcp = FastMCP(
    "mcp-zernio",
    instructions=_INSTRUCTIONS,
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
    import zernio_mcp.resources  # noqa: F401
    import zernio_mcp.prompts  # noqa: F401


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
