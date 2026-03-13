"""No-op auth provider for unauthenticated MCP servers."""


class NoAuthProvider:
    """Unauthenticated — no credentials injected.

    Use for local dev servers or MCP servers that accept anonymous access.
    """

    def get_headers(self) -> dict[str, str]:
        """Return empty headers (no auth)."""
        return {}

    def get_env_vars(self) -> dict[str, str]:
        """Return empty env vars (no auth)."""
        return {}

    def get_stdio_args(self) -> list[str]:
        """Return empty args (no auth)."""
        return []
