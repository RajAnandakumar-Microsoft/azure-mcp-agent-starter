"""MCP Server client for agent integration.

Provides HTTP and stdio client wrappers for calling MCP servers using JSON-RPC 2.0 protocol.
"""

import atexit
import json
import logging
import subprocess
import threading
from typing import Any

import requests

logger = logging.getLogger(__name__)

# Timeout bounds for MCP server calls (seconds).
_DEFAULT_TIMEOUT: int = 30
_MIN_TIMEOUT: int = 1
_MAX_TIMEOUT: int = 300

# Track all stdio clients for atexit cleanup.
_active_stdio_clients: list["StdioMCPClient"] = []
_cleanup_lock = threading.Lock()


class MCPError(Exception):
    """Raised when an MCP tool call fails.

    Provides a consistent error type for both HTTP and stdio transports.
    """

    def __init__(self, message: str, code: int | None = None) -> None:
        self.code = code
        super().__init__(message)


def _clamp_timeout(timeout: int | None) -> int:
    """Ensure timeout is within safe bounds."""
    if timeout is None:
        return _DEFAULT_TIMEOUT
    return max(_MIN_TIMEOUT, min(timeout, _MAX_TIMEOUT))


def _cleanup_stdio_clients() -> None:
    """Terminate all active stdio MCP server subprocesses on exit."""
    with _cleanup_lock:
        for client in _active_stdio_clients:
            try:
                client.close()
            except Exception:
                pass
        _active_stdio_clients.clear()


atexit.register(_cleanup_stdio_clients)


class MCPClient:
    """HTTP client for MCP server communication using JSON-RPC 2.0."""

    def __init__(self, base_url: str, function_key: str | None = None):
        """Initialize MCP client.

        Args:
            base_url: Base URL of the MCP server (e.g., http://localhost:7071/api)
            function_key: Optional Azure Function key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.function_key = function_key
        self.headers = {"Content-Type": "application/json"}
        if function_key:
            self.headers["x-functions-key"] = function_key
        self.request_id = 0

    def call_tool(
        self, tool_name: str, parameters: dict[str, Any], timeout: int | None = 30
    ) -> dict[str, Any]:
        """Call an MCP server tool using JSON-RPC 2.0 protocol.

        Args:
            tool_name: Name of the tool (e.g., 'search_requirements')
            parameters: Tool parameters as dictionary
            timeout: Request timeout in seconds (clamped to 1–300; None → 30)

        Returns:
            Tool response data (unwrapped from MCP content)

        Raises:
            MCPError: If the MCP server returns an error
            requests.RequestException: If the HTTP request itself fails
        """
        timeout = _clamp_timeout(timeout)
        self.request_id += 1

        jsonrpc_request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": parameters},
        }

        url = f"{self.base_url}/mcp"
        logger.debug("MCP HTTP → %s tool=%s", url, tool_name)

        response = requests.post(
            url, json=jsonrpc_request, headers=self.headers, timeout=timeout
        )
        response.raise_for_status()

        jsonrpc_response = response.json()

        if "error" in jsonrpc_response:
            error = jsonrpc_response["error"]
            raise MCPError(
                f"MCP tool error: {error.get('message', 'Unknown error')}",
                code=error.get("code"),
            )

        result = jsonrpc_response.get("result", {})

        if result.get("isError"):
            content = result.get("content", [{}])[0]
            error_data = json.loads(content.get("text", "{}"))
            raise MCPError(f"Tool execution error: {error_data.get('error')}")

        content = result.get("content", [{}])[0]
        data = json.loads(content.get("text", "{}"))
        logger.debug("MCP HTTP ← %s returned %d keys", tool_name, len(data))
        return data


class StdioMCPClient:
    """Stdio-based MCP client for subprocess communication using JSON-RPC 2.0."""

    def __init__(self, command: str, args: list[str], env: dict[str, str] | None = None):
        """Initialize stdio MCP client.

        Args:
            command: Command to run (e.g., "node")
            args: Command arguments (e.g., ["path/to/index.js", "org-name"])
            env: Optional environment variables to pass to the subprocess
        """
        self.command = command
        self.args = args
        self.env = env
        self.request_id = 0
        self.process: subprocess.Popen | None = None
        self._lock = threading.Lock()
        with _cleanup_lock:
            _active_stdio_clients.append(self)

    def _ensure_process(self) -> subprocess.Popen:
        """Ensure MCP server process is running (thread-safe)."""
        with self._lock:
            if self.process is None or self.process.poll() is not None:
                import os

                process_env = os.environ.copy()
                if self.env:
                    process_env.update(self.env)

                logger.debug("MCP stdio: spawning %s", self.command)
                self.process = subprocess.Popen(
                    [self.command] + self.args,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    env=process_env,
                )
                logger.debug("MCP stdio: spawned pid=%d", self.process.pid)
            return self.process

    def call_tool(
        self, tool_name: str, parameters: dict[str, Any], timeout: int | None = 30
    ) -> dict[str, Any]:
        """Call an MCP server tool using JSON-RPC 2.0 over stdio.

        Args:
            tool_name: Name of the tool (e.g., 'mcp_ado_wit_get_work_item')
            parameters: Tool parameters as dictionary
            timeout: Request timeout in seconds (clamped to 1–300; None → 30)

        Returns:
            Tool response data (unwrapped from MCP content)

        Raises:
            MCPError: If the MCP server returns an error or communication fails
        """
        timeout = _clamp_timeout(timeout)
        self.request_id += 1

        jsonrpc_request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": parameters},
        }

        process = self._ensure_process()
        logger.debug("MCP stdio → tool=%s pid=%d", tool_name, process.pid)

        request_line = json.dumps(jsonrpc_request) + "\n"
        process.stdin.write(request_line)
        process.stdin.flush()

        try:
            response_line = process.stdout.readline()
            if not response_line:
                raise MCPError("MCP server closed connection")

            jsonrpc_response = json.loads(response_line)
        except json.JSONDecodeError as e:
            raise MCPError(f"Invalid JSON response from MCP server: {e}")

        if "error" in jsonrpc_response:
            error = jsonrpc_response["error"]
            raise MCPError(
                f"MCP tool error: {error.get('message', 'Unknown error')}",
                code=error.get("code"),
            )

        result = jsonrpc_response.get("result", {})

        if result.get("isError"):
            content = result.get("content", [{}])[0]
            error_text = content.get("text", "Unknown MCP error")
            raise MCPError(f"MCP tool returned error: {error_text}")

        content = result.get("content", [])
        if not content:
            return {}

        text = content[0].get("text", "{}")
        data = json.loads(text)
        logger.debug("MCP stdio ← %s returned %d keys", tool_name, len(data))
        return data

    def close(self) -> None:
        """Close the MCP server process and unregister from cleanup list."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None
        with _cleanup_lock:
            if self in _active_stdio_clients:
                _active_stdio_clients.remove(self)


# MCP Server configurations
# Update these URLs when deployed to Azure
# Legacy HTTP-based config - kept for reference (JAMA/IcePanel demo servers)
# ADO now uses stdio transport configured in config.py
MCP_SERVERS = {
    "jama": {
        "base_url": "http://localhost:7071/api",
        "function_key": None,  # Add key when deployed
        "tools": ["search_requirements", "get_requirement", "list_related"],
    },
    # "ado": removed - now uses stdio transport (official Microsoft MCP)
    "icepanel": {
        "base_url": "http://localhost:7073/api",
        "function_key": None,  # Add key when deployed
        "tools": ["search_components", "get_component", "list_related"],
    },
}


def get_mcp_client(server_name: str) -> MCPClient | StdioMCPClient:
    """Get an MCP client for the specified server.

    Resolution order:
    1. Registry (mcp_servers.yaml) — auto-initialized on first call if the
       file exists at the repo root. Add new servers here without code changes.
    2. Legacy env-var config (backwards compatibility for jama/ado/icepanel).

    Args:
        server_name: Server label (e.g., "jama", "ado", "icepanel", or any
            label defined in mcp_servers.yaml).

    Returns:
        Configured MCPClient or StdioMCPClient instance.

    Raises:
        ValueError: If server_name is not found in the registry or legacy config.
    """
    import logging
    from pathlib import Path

    _logger = logging.getLogger(__name__)

    # --- 1. Try the server registry (mcp_servers.yaml) ---
    try:
        from agent_app.registry.server_registry import get_registry, init_registry

        registry = get_registry()
        if registry is None:
            # Auto-locate mcp_servers.yaml at the repo root (two levels up from
            # this file: agent_app/mcp_client.py → agent_app/ → repo root)
            yaml_path = Path(__file__).parent.parent / "mcp_servers.yaml"
            if yaml_path.exists():
                registry = init_registry(yaml_path)

        if registry is not None:
            try:
                return registry.get_client(server_name)
            except KeyError:
                _logger.debug(
                    "Server '%s' not in registry; falling back to legacy config.",
                    server_name,
                )
    except ImportError:
        # Registry module not available (shouldn't happen in normal installs)
        pass

    # --- 2. Legacy: build client from env-var config (jama / ado / icepanel) ---
    from agent_app.config import load_config

    config = load_config()

    if server_name == "jama":
        server_config = config.mcp.jama
    elif server_name == "ado":
        server_config = config.mcp.ado
    elif server_name == "icepanel":
        server_config = config.mcp.icepanel
    else:
        raise ValueError(
            f"Unknown MCP server: '{server_name}'. "
            f"Add an entry to mcp_servers.yaml or use one of: jama, ado, icepanel."
        )

    # Create appropriate client based on transport type
    if server_config.transport == "http":
        return MCPClient(server_config.url, None)
    elif server_config.transport == "stdio":
        return StdioMCPClient(
            server_config.command,
            server_config.args,
            env=server_config.env,
        )
    else:
        raise ValueError(f"Unknown transport type: {server_config.transport}")


# Tool function mapping for MCP servers
def search_requirements(query: str) -> dict[str, Any]:
    """Search for requirements via JAMA MCP server."""
    client = get_mcp_client("jama")
    return client.call_tool("search_requirements", {"query": query})


def get_requirement(requirement_id: str) -> dict[str, Any]:
    """Get requirement details via JAMA MCP server."""
    client = get_mcp_client("jama")
    return client.call_tool("get_requirement", {"requirement_id": requirement_id})


def search_work_items(query: str) -> dict[str, Any]:
    """Search for work items via ADO MCP server."""
    client = get_mcp_client("ado")
    return client.call_tool("search_work_items", {"query": query})


def get_work_item(work_item_id: str) -> dict[str, Any]:
    """Get work item details via ADO MCP server."""
    client = get_mcp_client("ado")
    return client.call_tool("get_work_item", {"work_item_id": work_item_id})


def search_components(query: str) -> dict[str, Any]:
    """Search for components via IcePanel MCP server."""
    client = get_mcp_client("icepanel")
    return client.call_tool("search_components", {"query": query})


def get_component(component_id: str) -> dict[str, Any]:
    """Get component details via IcePanel MCP server."""
    client = get_mcp_client("icepanel")
    return client.call_tool("get_component", {"component_id": component_id})


def list_related_artifacts(artifact_id: str) -> dict[str, Any]:
    """List related artifacts across all MCP servers.

    Determines which MCP server to call based on artifact ID prefix.

    Args:
        artifact_id: Artifact ID (REQ-*, WI-*, COMP-*, TEST-*)

    Returns:
        Related artifacts from appropriate MCP server
    """
    artifact_id_upper = artifact_id.upper()

    if artifact_id_upper.startswith("REQ-"):
        client = get_mcp_client("jama")
        return client.call_tool("list_related", {"requirement_id": artifact_id_upper})
    elif artifact_id_upper.startswith("WI-"):
        client = get_mcp_client("ado")
        return client.call_tool("list_related", {"work_item_id": artifact_id_upper})
    elif artifact_id_upper.startswith("COMP-"):
        client = get_mcp_client("icepanel")
        return client.call_tool("list_related", {"component_id": artifact_id_upper})
    else:
        return {
            "error": f"Unknown artifact type for ID: {artifact_id}",
            "found": False,
        }


# Tool function mapping (same interface as local tools)
MCP_TOOL_FUNCTIONS = {
    "search_requirements": search_requirements,
    "get_requirement": get_requirement,
    "search_work_items": search_work_items,
    "get_work_item": get_work_item,
    "search_components": search_components,
    "get_component": get_component,
    "list_related_artifacts": list_related_artifacts,
}
