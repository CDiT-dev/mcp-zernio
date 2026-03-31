"""Shared helpers for all tool modules."""

from __future__ import annotations

from zernio_mcp.client import ZernioClient, get_shared_client


def client() -> ZernioClient:
    return ZernioClient(http_client=get_shared_client())


def error(msg: str) -> dict:
    return {"error": msg}
