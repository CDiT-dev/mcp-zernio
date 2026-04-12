"""Configuration via pydantic-settings. All config from environment variables."""

from __future__ import annotations

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Zernio API
    zernio_api_key: SecretStr
    zernio_api_base: str = "https://zernio.com/api"

    # Transport
    mcp_transport: str = "stdio"  # "stdio" or "http"
    host: str = "0.0.0.0"
    port: int = 8717

    # Public URL (used in OAuth metadata — must be the external URL, not 0.0.0.0)
    public_url: str = "https://mcp-zernio.cdit-dev.de"

    # Inbox auth
    inbox_passphrase: str = ""  # Simple login passphrase for /inbox
    resend_api_key: str = ""    # Resend API key (magic links disabled if empty)
    inbox_email: str = ""       # Email address for magic link delivery


settings = Settings()  # type: ignore[call-arg]
