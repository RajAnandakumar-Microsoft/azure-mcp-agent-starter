"""Auth provider interface for per-MCP-server authentication.

Each MCP server may require a different authentication mechanism.
Auth providers are instantiated once per server and injected into
the transport layer (HTTP headers or stdio environment variables).
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class AuthProvider(Protocol):
    """Interface for per-server authentication.

    Implementors supply credentials in a transport-appropriate form:
    - HTTP transport: headers returned by get_headers()
    - stdio transport: env vars from get_env_vars() + CLI args from get_stdio_args()

    All methods must return safe empty dicts/lists when credentials are absent,
    so the transport still works (unauthenticated) rather than raising.
    """

    def get_headers(self) -> dict[str, str]:
        """HTTP request headers (for HTTP transport).

        Returns:
            Header name → value mapping, or empty dict if not applicable.
        """
        ...

    def get_env_vars(self) -> dict[str, str]:
        """Environment variables to inject into subprocess (for stdio transport).

        Returns:
            Env var name → value mapping, or empty dict if not applicable.
        """
        ...

    def get_stdio_args(self) -> list[str]:
        """Extra CLI arguments to append to the subprocess command (stdio transport).

        Returns:
            List of argument strings, or empty list if not applicable.
        """
        ...
