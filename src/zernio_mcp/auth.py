"""Authentication for the MCP server.

Uses OIDCProxy to proxy the OAuth flow to Keycloak using pre-registered
client credentials. Claude.ai (and Claude Code through it) authenticates
via the standard authorization_code flow.
"""

from __future__ import annotations

import logging

from fastmcp.server.auth.oidc_proxy import OIDCProxy

from zernio_mcp.config import settings

logger = logging.getLogger(__name__)


def build_auth() -> OIDCProxy | None:
    """Build the OIDCProxy authentication provider.

    Returns None for non-HTTP transport or if client secret is missing.
    """
    if settings.mcp_transport != "http":
        return None

    keycloak_client_secret = settings.keycloak_client_secret
    if not keycloak_client_secret:
        logger.warning(
            "KEYCLOAK_CLIENT_SECRET not set — OIDCProxy disabled"
        )
        return None

    config_url = f"{settings.keycloak_issuer}/.well-known/openid-configuration"
    return OIDCProxy(
        config_url=config_url,
        client_id=settings.keycloak_client_id,
        client_secret=keycloak_client_secret,
        base_url=settings.base_url,
    )
