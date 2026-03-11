"""
Configuration management for the Olympus Traceability Agent.

Loads environment variables and provides typed configuration objects.
"""

import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class AzureConfig:
    """Azure AI Foundry configuration."""

    project_endpoint: str
    agent_id: str
    subscription_id: str
    resource_group: str
    project_name: str

    def validate(self) -> None:
        """Validate that required configuration is present."""
        if not self.project_endpoint:
            logger.error("Missing required config: AZURE_EXISTING_AIPROJECT_ENDPOINT")
            sys.exit(1)
        if not self.agent_id:
            logger.error("Missing required config: AZURE_EXISTING_AGENT_ID")
            sys.exit(1)


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server."""

    transport: str  # "http" or "stdio"
    url: str | None = None  # For HTTP transport
    command: str | None = None  # For stdio transport (e.g., "node")
    args: list[str] | None = None  # For stdio transport
    env: dict[str, str] | None = None  # Environment variables for stdio transport


@dataclass
class MCPConfig:
    """MCP server configuration."""

    jama: MCPServerConfig
    ado: MCPServerConfig
    icepanel: MCPServerConfig


@dataclass
class AgentConfig:
    """Agent behavior configuration."""

    system_prompt: str
    max_tokens: int
    temperature: float


@dataclass
class AppConfig:
    """Root application configuration."""

    azure: AzureConfig
    agent: AgentConfig
    mcp: MCPConfig


def load_config() -> AppConfig:
    """
    Load configuration from environment variables.

    Looks for .env file in the current directory or parent directories.
    Returns typed AppConfig object.

    Raises:
        SystemExit: If required configuration is missing.
    """
    # Load .env file from current directory or parent
    dotenv_path = Path.cwd() / ".env"
    if not dotenv_path.exists():
        # Try parent directory (in case running from agent_app/)
        dotenv_path = Path.cwd().parent / ".env"

    if dotenv_path.exists():
        load_dotenv(dotenv_path)
        logger.info(f"Loaded environment from {dotenv_path}")
    else:
        logger.info("No .env file found, using system environment variables")

    # Azure AI Foundry configuration
    project_endpoint = os.getenv("AZURE_EXISTING_AIPROJECT_ENDPOINT", "")
    agent_id = os.getenv("AZURE_EXISTING_AGENT_ID", "")
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID", "")
    
    # Parse resource group and project name from endpoint or resource ID
    project_resource_id = os.getenv("AZURE_EXISTING_AIPROJECT_RESOURCE_ID", "")
    resource_group = ""
    project_name = ""
    
    if project_resource_id:
        # Parse: /subscriptions/{sub}/resourceGroups/{rg}/providers/.../projects/{name}
        parts = project_resource_id.split("/")
        if "resourceGroups" in parts:
            rg_idx = parts.index("resourceGroups")
            if rg_idx + 1 < len(parts):
                resource_group = parts[rg_idx + 1]
        if "projects" in parts:
            proj_idx = parts.index("projects")
            if proj_idx + 1 < len(parts):
                project_name = parts[proj_idx + 1]
    
    azure_config = AzureConfig(
        project_endpoint=project_endpoint,
        agent_id=agent_id,
        subscription_id=subscription_id,
        resource_group=resource_group,
        project_name=project_name,
    )

    # Validate required Azure configuration
    azure_config.validate()

    # Agent behavior configuration
    agent_config = AgentConfig(
        system_prompt=(
            "You are the Olympus Traceability Agent. You help users navigate "
            "and understand relationships across requirements, work items, tests, "
            "and architecture components. You provide summaries and deep links to "
            "artifacts. You never create, modify, or replace authoritative artifacts."
            "\n\n"
            "For now, you are in a setup phase. MCP server connections will be "
            "added in the next iteration."
        ),
        max_tokens=int(os.getenv("AGENT_MAX_TOKENS", "1000")),
        temperature=float(os.getenv("AGENT_TEMPERATURE", "0.7")),
    )

    # MCP server configuration
    ado_mcp_path = os.getenv("ADO_MCP_PATH", "")
    ado_org = os.getenv("ADO_ORG", "")
    ado_token = os.getenv("ADO_MCP_AUTH_TOKEN")  # Optional token for envvar auth

    # Unified demo server for JAMA and IcePanel
    demo_server_url = os.getenv("MCP_DEMO_URL", "http://localhost:7070/api")

    # Build ADO MCP arguments and environment
    ado_args = [ado_mcp_path, ado_org]
    ado_env = {}
    
    if ado_token:
        # Add --authentication envvar argument and set token in environment
        ado_args.extend(["--authentication", "envvar"])
        ado_env["ADO_MCP_AUTH_TOKEN"] = ado_token
        logger.info("Azure DevOps token loaded from environment (envvar auth)")

    mcp_config = MCPConfig(
        jama=MCPServerConfig(
            transport="http",
            url=demo_server_url,
        ),
        ado=MCPServerConfig(
            transport="stdio",
            command="node",
            args=ado_args,
            env=ado_env if ado_env else None,
        ),
        icepanel=MCPServerConfig(
            transport="http",
            url=demo_server_url,
        ),
    )

    config = AppConfig(azure=azure_config, agent=agent_config, mcp=mcp_config)
    logger.info("Configuration loaded successfully")
    return config
