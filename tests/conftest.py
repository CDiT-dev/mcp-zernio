"""Set required env vars before any test module imports settings."""

import os

os.environ.setdefault("ZERNIO_API_KEY", "test-key-for-testing")
os.environ.setdefault("MCP_TRANSPORT", "stdio")

import pytest
from zernio_mcp.client import _cache


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the TTL cache between tests."""
    _cache.clear()
    yield
    _cache.clear()
