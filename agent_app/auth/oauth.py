"""OAuth delegated auth provider using MSAL.

Acquires tokens via the MSAL (Microsoft Authentication Library) confidential
or public client flow. Tokens are cached in-memory and refreshed silently
when possible; interactive login is triggered only on first use or when the
cache is empty.

Config in mcp_servers.yaml::

    auth:
      type: oauth
      tenant_id: "your-tenant-id"
      client_id: "your-app-client-id"
      scopes:
        - "https://graph.microsoft.com/.default"
      client_secret_env_var: "MY_CLIENT_SECRET"   # omit for public/interactive

For Azure-native resources (ADO, Azure AI, etc.) prefer the ``azure_identity``
auth type instead, which uses ``DefaultAzureCredential``.

See: https://learn.microsoft.com/en-us/entra/identity-platform/msal-python
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# MSAL is an optional dependency — gracefully degrade if not installed.
try:
    import msal

    _MSAL_AVAILABLE = True
except ImportError:
    _MSAL_AVAILABLE = False


class OAuthAuthProvider:
    """OAuth delegated auth provider using MSAL.

    Supports two flows:
    - **Confidential client** (service-to-service): set ``client_secret_env_var``
      to the env var holding the client secret. Tokens are acquired via the
      client-credentials grant — no user interaction required.
    - **Public client** (interactive): omit ``client_secret_env_var``. On first
      call, MSAL opens a browser for interactive sign-in. Subsequent calls use
      the in-memory token cache (silent acquisition).

    Args:
        tenant_id: Azure AD / Entra ID tenant ID.
        client_id: App registration client ID.
        scopes: OAuth scopes to request (e.g., ``["https://graph.microsoft.com/.default"]``).
        client_secret_env_var: Env var holding the client secret (optional).
    """

    def __init__(
        self,
        tenant_id: str | None = None,
        client_id: str | None = None,
        scopes: list[str] | None = None,
        client_secret_env_var: str | None = None,
    ) -> None:
        self._tenant_id = tenant_id or "common"
        self._client_id = client_id or ""
        self._scopes = scopes or []
        self._client_secret_env_var = client_secret_env_var
        self._client_secret = (
            os.getenv(client_secret_env_var, "") if client_secret_env_var else ""
        )
        self._app: Any = None
        self._cached_token: str = ""

        if not _MSAL_AVAILABLE:
            logger.warning(
                "OAuthAuthProvider: 'msal' package is not installed. "
                "Run: pip install msal"
            )
        elif not self._client_id:
            logger.warning(
                "OAuthAuthProvider: client_id is not set — "
                "OAuth authentication will be skipped."
            )

    def _get_app(self) -> Any:
        """Lazily create and return the MSAL application instance."""
        if self._app is not None:
            return self._app

        authority = f"https://login.microsoftonline.com/{self._tenant_id}"

        if self._client_secret:
            self._app = msal.ConfidentialClientApplication(
                client_id=self._client_id,
                client_credential=self._client_secret,
                authority=authority,
            )
        else:
            self._app = msal.PublicClientApplication(
                client_id=self._client_id,
                authority=authority,
            )

        return self._app

    def _acquire_token(self) -> str:
        """Acquire a token, using cached/silent flow first.

        Returns:
            Access token string, or empty string on failure.
        """
        if not _MSAL_AVAILABLE or not self._client_id:
            return ""

        app = self._get_app()

        # Try silent acquisition from cache first
        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(self._scopes, account=accounts[0])
            if result and "access_token" in result:
                return result["access_token"]

        # Confidential client → client credentials grant
        if self._client_secret:
            result = app.acquire_token_for_client(scopes=self._scopes)
        else:
            # Public client → interactive browser login
            result = app.acquire_token_interactive(scopes=self._scopes)

        if result and "access_token" in result:
            return result["access_token"]

        error = result.get("error_description", result.get("error", "unknown"))
        logger.error("OAuth token acquisition failed: %s", error)
        return ""

    def get_headers(self) -> dict[str, str]:
        """Return Bearer auth header with an OAuth access token."""
        token = self._acquire_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    def get_env_vars(self) -> dict[str, str]:
        """Not used for OAuth (tokens are in headers)."""
        return {}

    def get_stdio_args(self) -> list[str]:
        """Not used for OAuth."""
        return []

    def validate(self) -> list[str]:
        """Return a list of configuration problems (empty if valid)."""
        issues: list[str] = []
        if not _MSAL_AVAILABLE:
            issues.append("'msal' package is not installed (pip install msal)")
        if not self._client_id:
            issues.append("client_id is not configured")
        if self._client_secret_env_var and not self._client_secret:
            issues.append(
                f"client_secret env var '{self._client_secret_env_var}' is not set"
            )
        return issues
