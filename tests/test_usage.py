"""Usage telemetry: one stderr JSON line per tool call."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from fastmcp import Client

from zernio_mcp.server import mcp

API_BASE = "https://zernio.com/api"


@respx.mock
@pytest.mark.asyncio
async def test_call_tool_writes_usage_line(capsys):
    respx.get(f"{API_BASE}/v1/profiles").mock(
        return_value=httpx.Response(200, json={"profiles": []})
    )
    async with Client(mcp) as c:
        await c.call_tool("profiles_list", {})
    lines = [json.loads(l) for l in capsys.readouterr().err.splitlines() if '"mcp_usage"' in l]
    assert len(lines) == 1
    assert lines[0]["server"] == "zernio"
    assert lines[0]["tool"] == "profiles_list"
    assert lines[0]["outcome"] == "ok"
