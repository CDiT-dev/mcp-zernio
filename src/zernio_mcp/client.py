"""Zernio REST API client with SSRF protection, retry, and sanitized errors."""

from __future__ import annotations

import asyncio
import ipaddress
import socket
import time
from typing import Any
from urllib.parse import urlparse

import httpx

from zernio_mcp.config import settings

ALLOWED_MEDIA_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif",
    "video/mp4", "video/quicktime", "video/webm",
}

MAX_MEDIA_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_RETRIES = 3
TIMEOUT = 30.0


class ZernioAPIError(Exception):
    """Sanitized API error — never contains secrets."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class SSRFError(Exception):
    """Raised when a URL fails SSRF validation."""


async def validate_url_for_ssrf(url: str) -> None:
    """Reject URLs that could cause SSRF attacks. Async to avoid blocking event loop."""
    parsed = urlparse(url)

    if parsed.scheme not in ("https",):
        raise SSRFError(f"Only HTTPS URLs are allowed, got: {parsed.scheme}")

    if not parsed.hostname:
        raise SSRFError("URL has no hostname")

    loop = asyncio.get_event_loop()
    try:
        addrinfo = await loop.run_in_executor(
            None, socket.getaddrinfo, parsed.hostname, None
        )
    except socket.gaierror:
        raise SSRFError(f"Cannot resolve hostname: {parsed.hostname}")

    for _, _, _, _, sockaddr in addrinfo:
        ip = ipaddress.ip_address(sockaddr[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise SSRFError(f"URL resolves to non-public IP: {ip}")


# PII fields to strip from account responses
_ACCOUNT_PII_FIELDS = {"email", "phone", "phoneNumber", "emailAddress"}


def strip_pii(data: dict[str, Any]) -> dict[str, Any]:
    """Remove PII fields from API response data."""
    return {k: v for k, v in data.items() if k not in _ACCOUNT_PII_FIELDS}


# ---------------------------------------------------------------------------
# Simple TTL cache for accounts/profiles (60s)
# ---------------------------------------------------------------------------

_cache: dict[str, tuple[float, Any]] = {}
_CACHE_TTL = 60.0


def cache_get(key: str) -> Any | None:
    entry = _cache.get(key)
    if entry:
        ts, value = entry[0], entry[1]
        ttl = entry[2] if len(entry) > 2 else _CACHE_TTL
        if (time.monotonic() - ts) < ttl:
            return value
    return None


def cache_set(key: str, value: Any, ttl: float | None = None) -> None:
    _cache[key] = (time.monotonic(), value, ttl or _CACHE_TTL)


def cache_invalidate(key: str) -> None:
    """Remove a specific key from the cache."""
    _cache.pop(key, None)


def cache_invalidate_prefix(prefix: str) -> None:
    """Remove all cache entries with keys starting with prefix."""
    to_remove = [k for k in _cache if k.startswith(prefix)]
    for k in to_remove:
        del _cache[k]


# ---------------------------------------------------------------------------
# Shared HTTP client (connection pooling)
# ---------------------------------------------------------------------------

_shared_client: httpx.AsyncClient | None = None


def get_shared_client() -> httpx.AsyncClient:
    global _shared_client
    if _shared_client is None or _shared_client.is_closed:
        _shared_client = httpx.AsyncClient(
            timeout=TIMEOUT,
            follow_redirects=False,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )
    return _shared_client


async def close_shared_client() -> None:
    global _shared_client
    if _shared_client and not _shared_client.is_closed:
        await _shared_client.aclose()
        _shared_client = None


class ZernioClient:
    """Async client for the Zernio REST API v1."""

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        self._base = settings.zernio_api_base.rstrip("/")
        self._api_key = settings.zernio_api_key
        self._http = http_client or get_shared_client()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a request with retry on 429 and sanitized errors."""
        url = f"{self._base}{path}"

        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = await self._http.request(
                    method, url, headers=self._headers(),
                    params=params, json=json_body,
                )

                if resp.status_code == 429 and attempt < MAX_RETRIES:
                    await asyncio.sleep(2**attempt)
                    continue

                if resp.status_code >= 400:
                    try:
                        body = resp.json()
                        msg = body.get("message", body.get("error", resp.text[:200]))
                    except Exception:
                        msg = resp.text[:200]
                    raise ZernioAPIError(
                        f"Zernio API error ({resp.status_code}): {msg}",
                        status_code=resp.status_code,
                    )

                if not resp.content or not resp.content.strip():
                    return {}
                try:
                    return resp.json()
                except Exception:
                    return {}

            except httpx.TimeoutException:
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(2**attempt)
                    continue
                raise ZernioAPIError("Zernio API request timed out after 30s")
            except httpx.HTTPError as e:
                raise ZernioAPIError(f"Network error: {type(e).__name__}")

        raise ZernioAPIError("Zernio API: max retries exceeded")

    async def get(self, path: str, **params: Any) -> dict[str, Any]:
        clean = {k: v for k, v in params.items() if v is not None}
        return await self._request("GET", path, params=clean or None)

    async def post(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("POST", path, json_body=body)

    async def put(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("PUT", path, json_body=body)

    async def patch(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("PATCH", path, json_body=body)

    async def delete(self, path: str, **params: Any) -> dict[str, Any]:
        clean = {k: v for k, v in params.items() if v is not None}
        return await self._request("DELETE", path, params=clean or None)

    # --- Media upload helpers ---

    async def presign_media(self, file_name: str, file_type: str) -> dict[str, Any]:
        return await self.post("/v1/media/presign", {"fileName": file_name, "fileType": file_type})

    async def upload_to_gcs(self, upload_url: str, data: bytes, content_type: str) -> None:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=False) as client:
            resp = await client.put(
                upload_url,
                content=data,
                headers={"Content-Type": content_type},
            )
            if resp.status_code >= 400:
                raise ZernioAPIError(
                    f"GCS upload failed ({resp.status_code})",
                    status_code=resp.status_code,
                )

    async def fetch_url_bytes(self, url: str) -> tuple[bytes, str]:
        """Fetch bytes from a URL with SSRF protection and size/type validation."""
        await validate_url_for_ssrf(url)

        async with httpx.AsyncClient(
            timeout=TIMEOUT, follow_redirects=False, max_redirects=0
        ) as client:
            resp = await client.get(url)

            content_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
            if content_type not in ALLOWED_MEDIA_TYPES:
                raise ZernioAPIError(
                    f"URL does not point to a supported media file. "
                    f"Got content-type: {content_type}. "
                    f"Supported: {', '.join(sorted(ALLOWED_MEDIA_TYPES))}"
                )

            data = resp.content
            if len(data) > MAX_MEDIA_SIZE:
                raise ZernioAPIError(
                    f"File exceeds 100MB limit ({len(data) / 1024 / 1024:.1f}MB)"
                )

            return data, content_type
