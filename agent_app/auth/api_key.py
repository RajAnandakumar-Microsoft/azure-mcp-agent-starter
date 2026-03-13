"""API key auth provider for MCP servers protected by a shared key header.

Typical use: Azure Function apps that require the 'x-functions-key' header.
"""

import logging
import os

logger = logging.getLogger(__name__)


class ApiKeyAuthProvider:
    """Injects an API key as an HTTP header.

    The key is read once at construction time from an environment variable.
    If the env var is absent, requests are sent without the header (so the
    server may reject them, but the agent starts normally).

    Args:
        header: HTTP header name (e.g., "x-functions-key" or "x-api-key").
        env_var: Name of the environment variable that holds the key.
    """

    def __init__(self, header: str, env_var: str) -> None:
        self._header = header
        self._key = os.getenv(env_var, "")
        if not self._key:
            logger.debug(
                "ApiKeyAuthProvider: env var '%s' is not set; "
                "requests to this server will be unauthenticated.",
                env_var,
            )

    def get_headers(self) -> dict[str, str]:
        """Return the API key header, or empty dict if key is not configured."""
        if self._key:
            return {self._header: self._key}
        return {}

    def get_env_vars(self) -> dict[str, str]:
        """Not used for HTTP transport."""
        return {}

    def get_stdio_args(self) -> list[str]:
        """Not used for HTTP transport."""
        return []
