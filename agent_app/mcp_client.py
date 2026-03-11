"""MCP Server client for agent integration.

Provides HTTP and stdio client wrappers for calling MCP servers using JSON-RPC 2.0 protocol.
"""

import json
import subprocess
from typing import Any

import requests


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
        self, tool_name: str, parameters: dict[str, Any], timeout: int = 30
    ) -> dict[str, Any]:
        """Call an MCP server tool using JSON-RPC 2.0 protocol.

        Args:
            tool_name: Name of the tool (e.g., 'search_requirements')
            parameters: Tool parameters as dictionary
            timeout: Request timeout in seconds

        Returns:
            Tool response data (unwrapped from MCP content)

        Raises:
            requests.RequestException: If request fails
            ValueError: If JSON-RPC response indicates error
        """
        # Increment request ID
        self.request_id += 1

        # Build JSON-RPC 2.0 request
        jsonrpc_request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": parameters},
        }

        # Send request to MCP endpoint
        url = f"{self.base_url}/mcp"
        response = requests.post(
            url, json=jsonrpc_request, headers=self.headers, timeout=timeout
        )
        response.raise_for_status()

        # Parse JSON-RPC response
        jsonrpc_response = response.json()

        # Check for JSON-RPC error
        if "error" in jsonrpc_response:
            error = jsonrpc_response["error"]
            raise ValueError(
                f"MCP tool error: {error.get('message', 'Unknown error')} "
                f"(code: {error.get('code')})"
            )

        # Extract result
        result = jsonrpc_response.get("result", {})

        # Check for MCP tool error
        if result.get("isError"):
            content = result.get("content", [{}])[0]
            error_data = json.loads(content.get("text", "{}"))
            raise ValueError(f"Tool execution error: {error_data.get('error')}")

        # Unwrap MCP content and return the actual data
        content = result.get("content", [{}])[0]
        return json.loads(content.get("text", "{}"))


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

    def _ensure_process(self) -> subprocess.Popen:
        """Ensure MCP server process is running."""
        if self.process is None or self.process.poll() is not None:
            import os
            # Merge custom env vars with current environment
            process_env = os.environ.copy()
            if self.env:
                process_env.update(self.env)
            
            self.process = subprocess.Popen(
                [self.command] + self.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=process_env,
            )
        return self.process

    def call_tool(
        self, tool_name: str, parameters: dict[str, Any], timeout: int = 30
    ) -> dict[str, Any]:
        """Call an MCP server tool using JSON-RPC 2.0 over stdio.

        Args:
            tool_name: Name of the tool (e.g., 'mcp_ado_wit_get_work_item')
            parameters: Tool parameters as dictionary
            timeout: Request timeout in seconds

        Returns:
            Tool response data (unwrapped from MCP content)

        Raises:
            RuntimeError: If process communication fails
            ValueError: If JSON-RPC response indicates error
        """
        # Increment request ID
        self.request_id += 1

        # Build JSON-RPC 2.0 request
        jsonrpc_request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": parameters},
        }

        # Ensure process is running
        process = self._ensure_process()

        # Send request to stdin
        request_line = json.dumps(jsonrpc_request) + "\n"
        process.stdin.write(request_line)
        process.stdin.flush()

        # Read response from stdout
        try:
            response_line = process.stdout.readline()
            if not response_line:
                raise RuntimeError("MCP server closed connection")

            jsonrpc_response = json.loads(response_line)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON response from MCP server: {e}")

        # Check for JSON-RPC error
        if "error" in jsonrpc_response:
            error = jsonrpc_response["error"]
            raise ValueError(
                f"MCP tool error: {error.get('message', 'Unknown error')} "
                f"(code: {error.get('code')})"
            )

        # Extract result
        result = jsonrpc_response.get("result", {})

        # Check for MCP tool error
        if result.get("isError"):
            content = result.get("content", [{}])[0]
            error_text = content.get("text", "Unknown MCP error")
            raise ValueError(f"MCP tool returned error: {error_text}")

        # Unwrap MCP content
        content = result.get("content", [])
        if not content:
            return {}

        # Return first content item's text as parsed JSON
        text = content[0].get("text", "{}")
        return json.loads(text)

    def close(self) -> None:
        """Close the MCP server process."""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            self.process = None


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

    Args:
        server_name: Name of MCP server (jama, ado, icepanel)

    Returns:
        Configured MCPClient or StdioMCPClient instance

    Raises:
        ValueError: If server_name is not recognized
    """
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
            f"Unknown MCP server: {server_name}. "
            f"Valid options: jama, ado, icepanel"
        )

    # Create appropriate client based on transport type
    if server_config.transport == "http":
        return MCPClient(server_config.url, None)
    elif server_config.transport == "stdio":
        return StdioMCPClient(
            server_config.command, 
            server_config.args,
            env=server_config.env
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
