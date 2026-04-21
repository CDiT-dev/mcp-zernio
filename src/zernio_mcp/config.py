"""Configuration via pydantic-settings. All config from environment variables."""

from __future__ import annotations

from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Zernio API
    zernio_api_key: SecretStr
    zernio_api_base: str = "https://zernio.com/api"

    # Transport
    mcp_transport: Literal["stdio", "http"] = "stdio"
    host: str = "127.0.0.1"
    port: int = 8717

    # Bearer token auth for MCP Portal
    mcp_api_key: SecretStr = SecretStr("")

    # Public URL (used in OAuth metadata — must be the external URL, not 0.0.0.0)
    public_url: str = "https://mcp-zernio.cdit-dev.de"

    # Inbox auth
    inbox_passphrase: SecretStr = SecretStr("")  # Simple login passphrase for /inbox
    resend_api_key: SecretStr = SecretStr("")    # Resend API key (magic links disabled if empty)
    inbox_email: str = ""                         # Email address for magic link delivery

    model_config = {"env_prefix": "", "case_sensitive": False}

    @model_validator(mode="after")
    def require_api_key_for_http(self) -> "Settings":
        if self.mcp_transport == "http" and not self.mcp_api_key.get_secret_value():
            raise ValueError(
                "MCP_API_KEY is required when MCP_TRANSPORT=http. "
                "Refusing to start an unauthenticated server."
            )
        return self


settings = Settings()  # type: ignore[call-arg]
