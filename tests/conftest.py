"""Set required env vars before any test module imports settings."""

import os

os.environ.setdefault("ZERNIO_API_KEY", "test-key-for-testing")
os.environ.setdefault("MCP_TRANSPORT", "stdio")
