"""OAuth / delegated auth provider stub.

Full delegated OAuth requires MSAL or Azure Identity SDK with a per-tenant
credential and a token cache. This stub logs a warning on construction and
returns empty credentials so the agent starts without blocking.

To implement delegated OAuth for a specific server:
1. Install msal: pip install msal
2. Create a PublicClientApplication with your tenant_id and client_id.
3. Call acquire_token_interactive() for the first sign-in; cache the result.
4. Call acquire_token_silent() on subsequent calls.
5. Replace get_headers() to return {"Authorization": "Bearer <access_token>"}.

For Azure resources (ADO, Azure AI, etc.) prefer DefaultAzureCredential /
AzureCliCredential from azure-identity, which handles multi-tenant silently
when `az login --tenant <tenant>` has been run.

For multi-tenant scenarios where users switch orgs:
- Maintain a token cache keyed by (tenant_id, client_id).
- Re-authenticate when the tenant context changes.

See: https://learn.microsoft.com/en-us/azure/active-directory/develop/msal-python
"""

import logging

logger = logging.getLogger(__name__)


class OAuthAuthProvider:
    """OAuth delegated auth provider — stub implementation.

    Args:
        tenant_id: Azure AD tenant ID (leave None for single-tenant defaults).
        client_id: App registration client ID.
        scopes: OAuth scopes to request (e.g., ["https://app/.default"]).
    """

    def __init__(
        self,
        tenant_id: str | None = None,
        client_id: str | None = None,
        scopes: list[str] | None = None,
    ) -> None:
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._scopes = scopes or []
        logger.warning(
            "OAuthAuthProvider for tenant=%s is a stub — requests will be "
            "unauthenticated. See agent_app/auth/oauth.py for implementation "
            "guidance.",
            tenant_id or "default",
        )

    def get_headers(self) -> dict[str, str]:
        """Return empty headers until full OAuth is implemented."""
        # TODO: replace with real token acquisition
        # token = self._acquire_token()
        # return {"Authorization": f"Bearer {token}"}
        return {}

    def get_env_vars(self) -> dict[str, str]:
        """Not used for OAuth (tokens are in headers)."""
        return {}

    def get_stdio_args(self) -> list[str]:
        """Not used for OAuth."""
        return []
