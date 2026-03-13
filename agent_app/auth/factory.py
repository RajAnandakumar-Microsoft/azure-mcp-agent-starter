"""Factory that builds the right AuthProvider from a server config dict."""

import logging
from typing import Any

from agent_app.auth.api_key import ApiKeyAuthProvider
from agent_app.auth.none_provider import NoAuthProvider
from agent_app.auth.oauth import OAuthAuthProvider
from agent_app.auth.pat import PatAuthProvider

logger = logging.getLogger(__name__)


def build_auth_provider(
    auth_config: dict[str, Any] | None,
) -> NoAuthProvider | ApiKeyAuthProvider | PatAuthProvider | OAuthAuthProvider:
    """Create an AuthProvider from a server config auth block.

    Config block shape (from mcp_servers.yaml ``auth:`` section):

    .. code-block:: yaml

        # No auth (local dev / anonymous servers)
        auth:
          type: none

        # API key injected as an HTTP header
        auth:
          type: api_key
          header: "x-functions-key"
          env_var: MY_FUNCTION_KEY

        # PAT injected via env var, with optional stdio flags
        auth:
          type: pat
          env_var: ADO_MCP_AUTH_TOKEN
          stdio_auth_flag: "--authentication"
          stdio_auth_value: "envvar"

        # OAuth delegated (stub — see oauth.py for full implementation)
        auth:
          type: oauth
          tenant_id: "your-tenant-id"
          client_id: "your-app-id"

    Args:
        auth_config: The parsed yaml ``auth`` dict, or None for no auth.

    Returns:
        An instantiated auth provider.
    """
    if not auth_config:
        return NoAuthProvider()

    auth_type = auth_config.get("type", "none")

    if auth_type == "none":
        return NoAuthProvider()

    if auth_type == "api_key":
        return ApiKeyAuthProvider(
            header=auth_config.get("header", "x-api-key"),
            env_var=auth_config.get("env_var", ""),
        )

    if auth_type == "pat":
        return PatAuthProvider(
            env_var=auth_config.get("env_var", ""),
            stdio_auth_flag=auth_config.get("stdio_auth_flag"),
            stdio_auth_value=auth_config.get("stdio_auth_value"),
        )

    if auth_type == "oauth":
        return OAuthAuthProvider(
            tenant_id=auth_config.get("tenant_id"),
            client_id=auth_config.get("client_id"),
            scopes=auth_config.get("scopes"),
        )

    logger.warning(
        "Unknown auth type %r in server config; falling back to no auth.", auth_type
    )
    return NoAuthProvider()
