"""Authentication for the MCP server.

Supports two authentication modes simultaneously via MultiAuth:

1. **Keycloak JWT** (for Claude.ai/Desktop connectors via OAuth):
   Validates JWT tokens issued by Keycloak using JWKS endpoint.

2. **Bearer token** (for Claude Code, n8n, and other direct clients):
   Static API key validation via Authorization: Bearer <key>.

No auth on stdio transport (local dev only).
"""

from __future__ import annotations

import hmac
import logging
import secrets

from zernio_mcp.config import settings

logger = logging.getLogger(__name__)


def build_auth():
    """Build FastMCP auth middleware. Returns None for stdio transport."""
    if settings.mcp_transport != "http":
        return None

    from fastmcp.server.auth import (
        AccessToken,
        JWTVerifier,
        MultiAuth,
        RemoteAuthProvider,
        TokenVerifier,
    )
    from pydantic import AnyHttpUrl

    class BearerTokenVerifier(TokenVerifier):
        """Validates incoming requests against a static API key."""

        def __init__(self, api_key: str) -> None:
            super().__init__()
            self._api_key = api_key

        async def verify_token(self, token: str) -> AccessToken | None:
            if not hmac.compare_digest(token, self._api_key):
                logger.warning("Rejected request with invalid API key")
                return None
            return AccessToken(
                token=token,
                client_id="mcp-zernio-client",
                scopes=["all"],
            )

    keycloak_issuer = settings.keycloak_issuer
    jwks_uri = f"{keycloak_issuer.rstrip('/')}/protocol/openid-connect/certs"

    jwt_verifier = JWTVerifier(
        jwks_uri=jwks_uri,
        issuer=keycloak_issuer,
        audience=settings.keycloak_audience,
    )

    keycloak_auth = RemoteAuthProvider(
        token_verifier=jwt_verifier,
        authorization_servers=[AnyHttpUrl(keycloak_issuer)],
        base_url=settings.base_url,
        scopes_supported=["openid"],
        resource_name="Zernio MCP Server",
    )

    verifiers: list[TokenVerifier] = []
    api_key = settings.mcp_zernio_api_key
    if api_key:
        verifiers.append(BearerTokenVerifier(api_key.get_secret_value()))

    return MultiAuth(server=keycloak_auth, verifiers=verifiers)


def generate_api_key() -> str:
    """Generate a cryptographically secure API key."""
    return f"zrmcp_{secrets.token_urlsafe(32)}"
