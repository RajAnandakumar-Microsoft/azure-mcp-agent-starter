"""Azure Identity auth provider using DefaultAzureCredential.

Uses the ``azure-identity`` SDK to acquire tokens for Azure-native services.
``DefaultAzureCredential`` tries multiple credential sources in order
(environment variables, managed identity, Azure CLI, etc.), so it works
seamlessly in local dev (``az login``) and deployed environments (managed
identity) without code changes.

Config in mcp_servers.yaml::

    auth:
      type: azure_identity
      scopes:
        - "https://management.azure.com/.default"

See: https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity
"""

import logging

logger = logging.getLogger(__name__)

# azure-identity is an optional dependency for auth.
try:
    from azure.identity import DefaultAzureCredential

    _AZURE_IDENTITY_AVAILABLE = True
except ImportError:
    _AZURE_IDENTITY_AVAILABLE = False


class AzureIdentityAuthProvider:
    """Auth provider using ``DefaultAzureCredential`` from azure-identity.

    This is the recommended auth type for Azure-native MCP servers
    (e.g., Azure DevOps, Azure AI, Azure Resource Manager) because it:
    - Works with ``az login`` in local dev
    - Uses managed identity in deployed environments
    - Handles token refresh automatically
    - Requires no client secrets or PATs

    Args:
        scopes: OAuth scopes to request
            (e.g., ``["https://management.azure.com/.default"]``).
    """

    def __init__(self, scopes: list[str] | None = None) -> None:
        self._scopes = scopes or []
        self._credential = None

        if not _AZURE_IDENTITY_AVAILABLE:
            logger.warning(
                "AzureIdentityAuthProvider: 'azure-identity' package is not "
                "installed. Run: pip install azure-identity"
            )
        elif not self._scopes:
            logger.warning(
                "AzureIdentityAuthProvider: no scopes configured — "
                "token acquisition will fail. Add a 'scopes' list to your "
                "auth config in mcp_servers.yaml."
            )

    def _get_credential(self) -> "DefaultAzureCredential":
        """Lazily create and return the DefaultAzureCredential."""
        if self._credential is None:
            self._credential = DefaultAzureCredential()
        return self._credential

    def _acquire_token(self) -> str:
        """Acquire a token using DefaultAzureCredential.

        Returns:
            Access token string, or empty string on failure.
        """
        if not _AZURE_IDENTITY_AVAILABLE or not self._scopes:
            return ""

        try:
            credential = self._get_credential()
            token = credential.get_token(*self._scopes)
            return token.token
        except Exception:
            logger.exception(
                "AzureIdentityAuthProvider: failed to acquire token. "
                "Ensure you are logged in (az login) or running with "
                "managed identity."
            )
            return ""

    def get_headers(self) -> dict[str, str]:
        """Return Bearer auth header using DefaultAzureCredential."""
        token = self._acquire_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    def get_env_vars(self) -> dict[str, str]:
        """Not used for Azure Identity (tokens are in headers)."""
        return {}

    def get_stdio_args(self) -> list[str]:
        """Not used for Azure Identity."""
        return []

    def validate(self) -> list[str]:
        """Return a list of configuration problems (empty if valid)."""
        issues: list[str] = []
        if not _AZURE_IDENTITY_AVAILABLE:
            issues.append(
                "'azure-identity' package is not installed "
                "(pip install azure-identity)"
            )
        if not self._scopes:
            issues.append("no scopes configured in auth config")
        return issues
