"""Smoke test — hits the real Zernio API to verify connectivity.

Run manually: uv run pytest tests/test_smoke.py -v
Skipped in CI unless ZERNIO_API_KEY is a real key (not the test placeholder).
"""

from __future__ import annotations

import os
import pytest
import httpx

from zernio_mcp.config import settings

REAL_KEY = os.environ.get("ZERNIO_API_KEY", "")
is_placeholder = not REAL_KEY or REAL_KEY == "test-key-for-testing"

pytestmark = pytest.mark.skipif(
    is_placeholder,
    reason="Skipped: ZERNIO_API_KEY is placeholder. Set a real key to run smoke tests.",
)


async def _get(path: str, **params) -> dict:
    """Make a direct API call with a fresh client (no shared state)."""
    base = settings.zernio_api_base.rstrip("/")
    headers = {
        "Authorization": f"Bearer {settings.zernio_api_key.get_secret_value()}",
        "Content-Type": "application/json",
    }
    clean = {k: v for k, v in params.items() if v is not None}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{base}{path}", headers=headers, params=clean or None)
        resp.raise_for_status()
        return resp.json()


@pytest.mark.asyncio
async def test_accounts_list_real():
    """Verify the Zernio API base URL and auth work against the real API."""
    data = await _get("/v1/accounts")

    assert "accounts" in data, f"Unexpected response shape: {list(data.keys())}"
    assert isinstance(data["accounts"], list)
    assert len(data["accounts"]) > 0, "No accounts connected — expected at least one"

    first = data["accounts"][0]
    assert "platform" in first, f"Account missing 'platform' field: {list(first.keys())}"
    assert "_id" in first, f"Account missing '_id' field: {list(first.keys())}"


@pytest.mark.asyncio
async def test_profiles_list_real():
    """Verify profiles endpoint returns valid data."""
    data = await _get("/v1/profiles")
    assert isinstance(data, dict), f"Expected dict, got {type(data)}"


@pytest.mark.asyncio
async def test_posts_list_real():
    """Verify posts endpoint returns valid paginated data."""
    data = await _get("/v1/posts", limit=1)
    assert isinstance(data, dict), f"Expected dict, got {type(data)}"
