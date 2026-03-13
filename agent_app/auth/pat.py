"""Personal Access Token (PAT) auth provider.

Supports two transport modes:
- HTTP: injects as 'Authorization: Bearer <token>' header.
- stdio: injects as an environment variable so the MCP server process can
  read it, plus optional CLI flags (e.g., --authentication envvar) for
  servers that require an explicit flag to activate env-var auth mode.
"""

import logging
import os

logger = logging.getLogger(__name__)


class PatAuthProvider:
    """PAT-based authentication for MCP servers.

    Args:
        env_var: Environment variable holding the PAT value.
        stdio_auth_flag: Optional CLI flag to enable env-var auth mode
            (e.g., "--authentication" for the official Azure DevOps MCP).
        stdio_auth_value: Value paired with stdio_auth_flag (e.g., "envvar").
        http_header: Header name for HTTP transport (default: "Authorization").
    """

    def __init__(
        self,
        env_var: str,
        stdio_auth_flag: str | None = None,
        stdio_auth_value: str | None = None,
        http_header: str = "Authorization",
    ) -> None:
        self._env_var = env_var
        self._token = os.getenv(env_var, "")
        self._stdio_auth_flag = stdio_auth_flag
        self._stdio_auth_value = stdio_auth_value
        self._http_header = http_header
        if not self._token:
            logger.debug(
                "PatAuthProvider: env var '%s' is not set; "
                "requests to this server may fail authentication.",
                env_var,
            )

    def get_headers(self) -> dict[str, str]:
        """Return Bearer auth header for HTTP transport."""
        if self._token:
            return {self._http_header: f"Bearer {self._token}"}
        return {}

    def get_env_vars(self) -> dict[str, str]:
        """Return token env var for stdio transport."""
        if self._token:
            return {self._env_var: self._token}
        return {}

    def get_stdio_args(self) -> list[str]:
        """Return optional auth CLI flags for stdio transport.

        Returns the flag pair only when a token is present, so the MCP
        subprocess is told which auth mechanism to use.
        """
        if self._token and self._stdio_auth_flag and self._stdio_auth_value:
            return [self._stdio_auth_flag, self._stdio_auth_value]
        return []
