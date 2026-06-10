"""Tag-profile tests for the shelf 'tool tags' refinement.

Deployers gate a read-only / write / destructive surface via fastmcp
include_tags / exclude_tags. These tests pin the semantic tag contract on the
*registered* tools (the metadata the Cloudflare MCP Portal and any deployer
actually sees), not just the source text.

Contract:
  - every tool carries exactly one of {"read", "write"};
  - pure reads carry "read" (and never "write" / "destructive");
  - mutating tools carry "write" + "social";
  - delete / clear tools additionally carry "destructive".
"""

from __future__ import annotations

import pytest

import zernio_mcp.tools  # noqa: F401  -- import for registration side effects
from zernio_mcp.server import mcp

# The destructive surface, per the shelf brief.
DESTRUCTIVE_TOOLS = {
    "posts_delete",
    "comments_delete",
    "accounts_delete",
    "broadcasts_delete",
    "contacts_delete",
    "profiles_delete",
    "webhooks_delete",
    "queue_delete_slot",
    "inbox_message_delete",
    "queue_clear",
}


async def _registered_tools() -> dict[str, set[str]]:
    """Map tool name -> set(tags) from the registered FunctionTool objects."""
    tools = await mcp._list_tools()
    return {t.name: set(t.tags or ()) for t in tools}


@pytest.mark.asyncio
async def test_every_tool_has_read_or_write_exactly_once():
    tags_by_name = await _registered_tools()
    assert tags_by_name, "no tools registered"
    for name, tags in tags_by_name.items():
        rw = {"read", "write"} & tags
        assert len(rw) == 1, f"{name} must carry exactly one of read/write, got {sorted(tags)}"


@pytest.mark.asyncio
async def test_destructive_tools_tagged_write_and_destructive():
    tags_by_name = await _registered_tools()
    missing = [
        name for name in DESTRUCTIVE_TOOLS
        if not {"write", "destructive"} <= tags_by_name.get(name, set())
    ]
    assert not missing, f"delete tools missing write+destructive tags: {missing}"
    # And destructive is mutating, so it must carry the 'social' profile tag too.
    for name in DESTRUCTIVE_TOOLS:
        assert "social" in tags_by_name[name], f"{name} missing 'social' tag"


@pytest.mark.asyncio
async def test_only_delete_tools_are_destructive():
    """A read-only deployer excludes 'destructive'; nothing benign may carry it."""
    tags_by_name = await _registered_tools()
    unexpected = [
        name for name, tags in tags_by_name.items()
        if "destructive" in tags and name not in DESTRUCTIVE_TOOLS
    ]
    assert not unexpected, f"non-delete tools wrongly tagged destructive: {unexpected}"


@pytest.mark.asyncio
async def test_read_profile_never_mutates():
    """include_tags={'read'} must select a surface with no write/destructive tools."""
    tags_by_name = await _registered_tools()
    read_surface = {n for n, t in tags_by_name.items() if "read" in t}
    assert read_surface, "no read tools found"
    for name in read_surface:
        tags = tags_by_name[name]
        assert "write" not in tags, f"{name} is in read profile but also tagged write"
        assert "destructive" not in tags, f"{name} is in read profile but also tagged destructive"


@pytest.mark.asyncio
async def test_destructive_subset_of_write_profile():
    """Every destructive tool is also in the broader 'write' profile."""
    tags_by_name = await _registered_tools()
    write_surface = {n for n, t in tags_by_name.items() if "write" in t}
    assert DESTRUCTIVE_TOOLS <= write_surface
