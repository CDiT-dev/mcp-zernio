"""Configuration via pydantic-settings. All config from environment variables."""

from __future__ import annotations

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Zernio API
    zernio_api_key: SecretStr
    zernio_api_base: str = "https://api.zernio.com"

    # Bearer token (for Claude Code, n8n, direct clients)
    mcp_zernio_api_key: SecretStr | None = None

    # Keycloak JWT (for Claude.ai/Desktop via OAuth)
    keycloak_issuer: str = ""
    keycloak_audience: str = "mcp-zernio"

    # Transport
    mcp_transport: str = "stdio"  # "stdio" or "http"
    host: str = "0.0.0.0"
    port: int = 8717

    # Public URL (used in OAuth metadata — must be the external URL, not 0.0.0.0)
    public_url: str = "https://mcp-zernio.cdit-dev.de"

    @property
    def base_url(self) -> str:
        return self.public_url


settings = Settings()  # type: ignore[call-arg]
