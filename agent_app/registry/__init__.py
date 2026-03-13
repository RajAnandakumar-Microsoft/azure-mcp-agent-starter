"""MCP Server Registry package.

Provides a config-driven registry that maps server labels to MCP clients.
Define servers in mcp_servers.yaml at the repo root; no code changes needed
when adding new MCP servers.
"""

from agent_app.registry.server_registry import (
    ServerRegistry,
    get_client,
    get_registry,
    init_registry,
)

__all__ = [
    "ServerRegistry",
    "get_registry",
    "init_registry",
    "get_client",
]
