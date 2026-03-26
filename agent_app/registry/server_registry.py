"""MCP Server Registry — loads server definitions from YAML and manages clients.

The registry is the single point of truth for which MCP servers exist,
how to reach them, and how to authenticate with them. Application code
calls ``get_mcp_client(label)`` without knowing anything about transport,
URLs, or credentials.

Typical usage (auto-initialized from mcp_servers.yaml at startup)::

    from agent_app.registry.server_registry import get_client

    client = get_client("ado")
    result = client.call_tool("search_workitem", {"searchText": "login bug"})

Adding a new server requires only a new entry in mcp_servers.yaml — no
code changes.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any

import yaml

from agent_app.auth.factory import build_auth_provider
from agent_app.mcp_client import MCPClient, StdioMCPClient

logger = logging.getLogger(__name__)

# Tool name prefixes that indicate write/mutation operations.
# These are blocked when a server is configured as read_only (the default).
_WRITE_PREFIXES: tuple[str, ...] = (
    "create_",
    "update_",
    "delete_",
    "patch_",
    "put_",
    "post_",
    "insert_",
    "remove_",
    "add_",
    "edit_",
    "write_",
    "save_",
    "publish_",
    "set_",
    "reset_",
)

# Matches ${VAR} and ${VAR:-default} placeholders
_ENV_VAR_PATTERN = re.compile(r"\$\{([^}:-]+)(?::-([^}]*))?\}")


def _interpolate(value: str) -> str:
    """Expand ``${VAR}`` and ``${VAR:-default}`` placeholders using os.environ.

    ``${VAR:-default}`` semantics: use VAR if set and non-empty, else default.
    """

    def replacer(m: re.Match) -> str:
        var_name = m.group(1)
        default = m.group(2) if m.group(2) is not None else ""
        return os.environ.get(var_name) or default

    return _ENV_VAR_PATTERN.sub(replacer, value)


def _is_write_tool(tool_name: str) -> bool:
    """Return True if the tool name matches a known write/mutation prefix."""
    lower = tool_name.lower()
    return any(lower.startswith(prefix) for prefix in _WRITE_PREFIXES)


class ServerRegistry:
    """Registry of MCP servers loaded from a YAML configuration file.

    Responsibilities:
    - Parse ``mcp_servers.yaml`` into server definitions.
    - Instantiate ``MCPClient`` (HTTP) or ``StdioMCPClient`` (stdio) per server.
    - Apply per-server auth providers (api_key, pat, oauth, none).
    - Cache client instances (one per label, created on first access).
    - Enforce read-only safety by filtering write-prefixed tool names.

    Example YAML entry::

        servers:
          - label: my_server
            description: "My custom MCP server"
            transport: http
            url: "https://my-server.azurewebsites.net/api"
            auth:
              type: api_key
              header: "x-functions-key"
              env_var: MY_SERVER_FUNCTION_KEY
            read_only: true
    """

    def __init__(self, server_definitions: list[dict[str, Any]]) -> None:
        # Index by label for O(1) lookups
        self._definitions: dict[str, dict[str, Any]] = {
            s["label"]: s for s in server_definitions
        }
        # Cache: label → instantiated client
        self._clients: dict[str, MCPClient | StdioMCPClient] = {}

    @classmethod
    def from_yaml(cls, path: str | Path) -> "ServerRegistry":
        """Load server definitions from a YAML file.

        Args:
            path: Absolute or relative path to mcp_servers.yaml.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the YAML is missing the ``servers`` key.
        """
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(
                f"MCP server config not found: {config_path.resolve()}"
            )

        with config_path.open(encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        servers = raw.get("servers", [])
        if not isinstance(servers, list):
            raise ValueError(
                f"mcp_servers.yaml must contain a 'servers' list. Got: {type(servers)}"
            )

        logger.info(
            "ServerRegistry: loaded %d server definition(s) from %s",
            len(servers),
            config_path.resolve(),
        )
        return cls(servers)

    @classmethod
    def from_yaml_if_exists(cls, path: str | Path) -> "ServerRegistry | None":
        """Load from YAML if the file exists; return None otherwise.

        Use this for optional / graceful-degradation initialization.
        """
        try:
            return cls.from_yaml(path)
        except FileNotFoundError:
            return None

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def labels(self) -> list[str]:
        """Return all registered server label strings."""
        return list(self._definitions.keys())

    def get_definition(self, label: str) -> dict[str, Any] | None:
        """Return the raw server definition dict for a label, or None."""
        return self._definitions.get(label)

    def is_read_only(self, label: str) -> bool:
        """Return True if the server is configured as read-only (default: True)."""
        return bool(self._definitions.get(label, {}).get("read_only", True))

    def is_tool_allowed(self, label: str, tool_name: str) -> bool:
        """Return True if the tool is permitted for this server.

        In read-only mode (the default), any tool whose name starts with a
        write/mutation prefix is blocked. A warning is logged.
        """
        if self.is_read_only(label) and _is_write_tool(tool_name):
            logger.warning(
                "Blocked write tool '%s' on read-only server '%s'. "
                "If this tool is required, set read_only: false in mcp_servers.yaml "
                "(not recommended).",
                tool_name,
                label,
            )
            return False
        return True

    def validate_credentials(self) -> dict[str, list[str]]:
        """Check all servers for auth configuration problems.

        Builds the auth provider for each registered server and calls its
        ``validate()`` method (if available). Returns a dict mapping server
        labels to lists of issue descriptions. Servers with no issues are
        omitted.

        Call this at startup to fail fast with clear error messages::

            issues = registry.validate_credentials()
            if issues:
                for label, problems in issues.items():
                    for p in problems:
                        logger.error("Server '%s': %s", label, p)

        Returns:
            ``{label: [problem, ...]}`` for servers with issues; empty dict
            if everything looks good.
        """
        all_issues: dict[str, list[str]] = {}

        for label, defn in self._definitions.items():
            auth = build_auth_provider(defn.get("auth"))
            validate_fn = getattr(auth, "validate", None)
            if callable(validate_fn):
                issues = validate_fn()
                if issues:
                    all_issues[label] = issues

        return all_issues

    # ------------------------------------------------------------------
    # Client access
    # ------------------------------------------------------------------

    def get_client(self, label: str) -> MCPClient | StdioMCPClient:
        """Return (and cache) an MCP client for the given server label.

        Clients are created lazily on first access and reused on subsequent
        calls, so a single client instance is shared across the process.

        Args:
            label: Server label as defined in mcp_servers.yaml.

        Raises:
            KeyError: If no server with this label is registered.
            ValueError: If the server definition is invalid (bad transport, etc.).
        """
        if label in self._clients:
            return self._clients[label]

        defn = self._definitions.get(label)
        if defn is None:
            known = ", ".join(self._definitions) or "(none)"
            raise KeyError(
                f"MCP server '{label}' is not registered. "
                f"Known servers: {known}. "
                f"Add an entry to mcp_servers.yaml to register it."
            )

        client = self._build_client(label, defn)
        self._clients[label] = client
        return client

    def _build_client(
        self, label: str, defn: dict[str, Any]
    ) -> MCPClient | StdioMCPClient:
        """Instantiate the correct transport client for a server definition."""
        transport = defn.get("transport", "http")
        auth = build_auth_provider(defn.get("auth"))

        if transport == "http":
            url = _interpolate(defn.get("url", ""))
            if not url:
                raise ValueError(
                    f"Server '{label}': 'url' is required for HTTP transport."
                )
            # MCPClient accepts function_key as a positional arg; everything
            # else goes into .headers. We extract the two common key headers
            # so they map to the MCPClient constructor param.
            headers = auth.get_headers()
            function_key = headers.get("x-functions-key") or headers.get("x-api-key")

            # Any remaining headers (e.g., Authorization for Bearer tokens)
            skip = {"x-functions-key", "x-api-key"}
            extra_headers = {k: v for k, v in headers.items() if k not in skip}

            client = MCPClient(base_url=url, function_key=function_key)
            if extra_headers:
                client.headers.update(extra_headers)

            logger.debug("Registry: HTTP client for '%s' → %s", label, url)
            return client

        if transport == "stdio":
            command = _interpolate(defn.get("command", ""))
            raw_args: list[str] = defn.get("args", [])
            args = [_interpolate(a) for a in raw_args]

            # Append auth CLI flags (e.g., --authentication envvar)
            auth_args = auth.get_stdio_args()
            if auth_args:
                args = args + auth_args

            env_vars = auth.get_env_vars()
            client = StdioMCPClient(
                command=command, args=args, env=env_vars or None
            )
            logger.debug(
                "Registry: stdio client for '%s' → %s %s", label, command, args
            )
            return client

        raise ValueError(
            f"Server '{label}': unknown transport '{transport}'. "
            f"Supported transports: http, stdio."
        )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_REGISTRY: ServerRegistry | None = None


def get_registry() -> ServerRegistry | None:
    """Return the module-level registry singleton, or None if not initialized."""
    return _REGISTRY


def init_registry(path: str | Path) -> ServerRegistry:
    """Initialize the module-level registry from a YAML file.

    Call this once at application startup (before any ``get_client`` calls).
    Subsequent calls replace the existing registry.

    Args:
        path: Path to mcp_servers.yaml.

    Returns:
        The initialized ServerRegistry.
    """
    global _REGISTRY
    _REGISTRY = ServerRegistry.from_yaml(path)
    logger.info(
        "ServerRegistry initialized. Registered servers: %s",
        _REGISTRY.labels(),
    )
    return _REGISTRY


def get_client(label: str) -> MCPClient | StdioMCPClient:
    """Convenience wrapper: get a client from the module-level registry.

    Auto-initializes the registry from ``mcp_servers.yaml`` at the repo root
    on first call if the registry has not been explicitly initialized.

    Args:
        label: Server label (e.g., "ado", "jama", "icepanel").

    Raises:
        KeyError: If the label is not registered.
        FileNotFoundError: If mcp_servers.yaml cannot be found.
    """
    global _REGISTRY
    if _REGISTRY is None:
        # Auto-locate mcp_servers.yaml relative to this file's package root
        default_path = Path(__file__).parent.parent.parent / "mcp_servers.yaml"
        if default_path.exists():
            _REGISTRY = ServerRegistry.from_yaml(default_path)
        else:
            raise FileNotFoundError(
                "mcp_servers.yaml not found. Either place it at the repo root "
                "or call init_registry(path) before using get_client()."
            )
    return _REGISTRY.get_client(label)
