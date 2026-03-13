"""Agent tool definitions using MCP server clients.

These tools call MCP servers (JAMA, ADO, IcePanel) using JSON-RPC 2.0 protocol.
MCP servers must be running locally or deployed to Azure Functions.
"""

import asyncio
import logging
from typing import Any

from azure.ai.agents.models import FunctionDefinition, FunctionToolDefinition

from agent_app.mcp_client import get_mcp_client
from agent_app.mcp_utils import fetch_related_artifacts_parallel

logger = logging.getLogger(__name__)


def search_requirements(query: str) -> dict[str, Any]:
    """Search for requirements in JAMA by keyword or ID.

    Searches requirement titles and descriptions for matches.
    Returns matching requirements with IDs, titles, and deep links.

    Args:
        query: Search keyword or requirement ID (e.g., 'authentication', 'REQ-001')

    Returns:
        Dictionary with source_system, results list, and match count
    """
    client = get_mcp_client("jama")
    return client.call_tool("search_requirements", {"query": query})


def get_requirement(requirement_id: str) -> dict[str, Any]:
    """Retrieve a specific requirement by ID from JAMA.

    Returns full requirement details including title, description,
    status, priority, relationships, and deep link.

    Args:
        requirement_id: The requirement ID (e.g., 'REQ-001')

    Returns:
        Dictionary with requirement details or error if not found
    """
    client = get_mcp_client("jama")
    return client.call_tool("get_requirement", {"requirement_id": requirement_id})


def list_related_requirements(requirement_id: str) -> dict[str, Any]:
    """List all artifacts (work items, components) related to a JAMA requirement.

    Args:
        requirement_id: The requirement ID (e.g., 'REQ-001')

    Returns:
        Dictionary with related artifacts grouped by type
    """
    client = get_mcp_client("jama")
    return client.call_tool("list_related_requirements", {"id": requirement_id})


def find_requirements_by_work_item(work_item_id: str) -> dict[str, Any]:
    """Find JAMA requirements that reference a specific work item.
    
    Use this when you need to discover which requirements are linked to a work item.

    Args:
        work_item_id: Work item ID with or without WI- prefix (e.g., '9', 'WI-9')

    Returns:
        Dictionary with matching requirements that reference this work item
    """
    client = get_mcp_client("jama")
    return client.call_tool("find_requirements_by_work_item", {"work_item_id": work_item_id})


def search_work_items(query: str) -> dict[str, Any]:
    """Search for work items in Azure DevOps by keyword, ID, or assignee name.

    Searches work item titles, descriptions, assigned users, types, and states
    across stories, tasks, bugs. Returns matching work items with IDs, types,
    states, assignees, and deep links.

    Args:
        query: Search keyword, work item ID, or person name (e.g., 'OAuth', 'WI-101', 'Jane Smith')

    Returns:
        Dictionary with source_system, results list, and match count
    """
    client = get_mcp_client("ado")
    return client.call_tool("search_workitem", {"searchText": query})


def get_my_work_items(project: str = "pocdemo", include_completed: bool = False) -> dict[str, Any]:
    """Get work items assigned to the current user in Azure DevOps.

    Args:
        project: Project name (default: "pocdemo")
        include_completed: Whether to include completed work items

    Returns:
        Dictionary with list of assigned work items
    """
    client = get_mcp_client("ado")
    return client.call_tool("wit_my_work_items", {
        "project": project,
        "includeCompleted": include_completed
    })


def get_work_item(work_item_id: str, project: str = "pocdemo") -> dict[str, Any]:
    """Retrieve a specific work item by ID from Azure DevOps.

    Returns full work item details including type, title, state,
    assignment, relationships, and deep link.

    Args:
        work_item_id: The work item ID (e.g., 'WI-101' or '101')
        project: The Azure DevOps project name (default: 'pocdemo')

    Returns:
        Dictionary with work item details or error if not found
    """
    client = get_mcp_client("ado")
    # Convert to int if it's a numeric string
    try:
        id_num = int(work_item_id.replace("WI-", "").replace("#", ""))
    except ValueError:
        id_num = work_item_id
    return client.call_tool("wit_get_work_item", {"id": id_num, "project": project})


def search_components(query: str) -> dict[str, Any]:
    """Search for architecture components in IcePanel by keyword or ID.

    Searches component names and descriptions across microservices,
    libraries, gateways. Returns matching components with deep links.

    Args:
        query: Search keyword or component ID (e.g., 'authentication', 'COMP-201')

    Returns:
        Dictionary with source_system, results list, and match count
    """
    client = get_mcp_client("icepanel")
    return client.call_tool("search_components", {"query": query})


def get_component(component_id: str) -> dict[str, Any]:
    """Retrieve a specific architecture component by ID from IcePanel.

    Returns full component details including name, type, technology,
    relationships, and deep link.

    Args:
        component_id: The component ID (e.g., 'COMP-201')

    Returns:
        Dictionary with component details or error if not found
    """
    client = get_mcp_client("icepanel")
    return client.call_tool("get_component", {"id": component_id})


def list_related_artifacts(artifact_id: str) -> dict[str, Any]:
    """List all artifacts related to a given requirement, work item, component, or test.

    Traverses relationships to find connected artifacts across systems.
    Fetches related artifacts from multiple systems in parallel for faster response.
    Returns 1-hop neighbors with IDs, titles, and deep links.

    Args:
        artifact_id: The artifact ID (e.g., 'REQ-001', 'WI-101', 'COMP-201')

    Returns:
        Dictionary with related artifacts grouped by source system
    """
    logger.info(
        f"[TOOL] list_related_artifacts called with artifact_id={artifact_id}"
    )

    try:
        # 1. Determine source system and fetch base artifact
        if artifact_id.startswith("REQ-"):
            client = get_mcp_client("jama")
            base_artifact = client.call_tool(
                "get_requirement", {"requirement_id": artifact_id}
            )
        elif artifact_id.startswith("WI-") or artifact_id.isdigit():
            client = get_mcp_client("ado")
            work_item_id = artifact_id.replace("WI-", "")
            base_artifact = client.call_tool(
                "wit_get_work_item",
                {"work_item_id": work_item_id, "project": "DemoProject"},
            )
        elif artifact_id.startswith("COMP-"):
            client = get_mcp_client("icepanel")
            base_artifact = client.call_tool(
                "get_component", {"component_id": artifact_id}
            )
        else:
            return {
                "source_system": "unknown",
                "error": f"Unknown artifact ID format: {artifact_id}",
                "artifact_id": artifact_id,
            }

        if not base_artifact:
            return {
                "source_system": "unknown",
                "error": f"Artifact {artifact_id} not found",
                "artifact_id": artifact_id,
            }

        # 2. Fetch related artifacts in parallel using asyncio
        result = asyncio.run(fetch_related_artifacts_parallel(base_artifact))

        logger.info(
            f"[TOOL] list_related_artifacts returning "
            f"{len(result['related_artifacts'])} related artifacts "
            f"(JAMA: {result['counts']['jama']}, "
            f"ADO: {result['counts']['ado']}, "
            f"IcePanel: {result['counts']['icepanel']})"
        )

        return result

    except Exception as e:
        logger.error(
            f"[TOOL] list_related_artifacts failed for {artifact_id}: {e}",
            exc_info=True,
        )
        return {
            "source_system": "unknown",
            "error": str(e),
            "artifact_id": artifact_id,
        }


# Tool definitions for AgentsClient
def get_tool_definitions() -> list[FunctionToolDefinition]:
    """Return tool definitions for the agent.

    These tools are registered with the agent to enable tool calling.
    Each tool includes name, description, and parameter schema.
    """
    return [
        FunctionToolDefinition(
            function=FunctionDefinition(
                name="search_requirements",
                description="Search for requirements in JAMA by keyword or ID. Searches requirement titles and descriptions for matches. Returns matching requirements with IDs, titles, and deep links.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search keyword or requirement ID (e.g., 'authentication', 'REQ-001')",
                        },
                    },
                    "required": ["query"],
                },
            )
        ),
        FunctionToolDefinition(
            function=FunctionDefinition(
                name="get_requirement",
                description="Retrieve a specific requirement by ID from JAMA. Returns full requirement details including title, description, status, priority, relationships, and deep link.",
                parameters={
                    "type": "object",
                    "properties": {
                        "requirement_id": {
                            "type": "string",
                            "description": "The requirement ID (e.g., 'REQ-001')",
                        },
                    },
                    "required": ["requirement_id"],
                },
            )
        ),
        FunctionToolDefinition(
            function=FunctionDefinition(
                name="list_related_requirements",
                description="List all artifacts (work items, components) related to a JAMA requirement. Returns work items, components, and other requirements linked to the specified requirement ID.",
                parameters={
                    "type": "object",
                    "properties": {
                        "requirement_id": {
                            "type": "string",
                            "description": "The requirement ID (e.g., 'REQ-001')",
                        },
                    },
                    "required": ["requirement_id"],
                },
            )
        ),
        FunctionToolDefinition(
            function=FunctionDefinition(
                name="find_requirements_by_work_item",
                description="Find JAMA requirements that reference a specific Azure DevOps work item. Use this when you need to discover which requirements are linked to a work item.",
                parameters={
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "string",
                            "description": "Work item ID with or without WI- prefix (e.g., '9', 'WI-9', '10')",
                        },
                    },
                    "required": ["work_item_id"],
                },
            )
        ),
        FunctionToolDefinition(
            function=FunctionDefinition(
                name="search_work_items",
                description="Search for work items in Azure DevOps by keyword or ID. Searches work item titles and descriptions across stories, tasks, bugs. Returns matching work items with IDs, types, states, and deep links.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search keyword or work item ID (e.g., 'OAuth', 'WI-101')",
                        },
                    },
                    "required": ["query"],
                },
            )
        ),
        FunctionToolDefinition(
            function=FunctionDefinition(
                name="get_work_item",
                description="Retrieve a specific work item by ID from Azure DevOps. Returns full work item details including type, title, state, assignment, relationships, and deep link.",
                parameters={
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "string",
                            "description": "The work item ID (e.g., 'WI-101')",
                        },
                    },
                    "required": ["work_item_id"],
                },
            )
        ),
        FunctionToolDefinition(
            function=FunctionDefinition(
                name="get_my_work_items",
                description="Get ALL work items assigned to the current authenticated user in Azure DevOps. Use this when user asks about 'my work items', 'bugs assigned to me', 'my tasks', 'items assigned to me', or similar queries about their own work. Returns complete list of assigned work items including bugs, tasks, epics, and stories with IDs, types, titles, states, and descriptions. Optionally include completed work items.",
                parameters={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string",
                            "description": "Project name (default: 'pocdemo')",
                        },
                        "include_completed": {
                            "type": "boolean",
                            "description": "Whether to include completed work items (default: false)",
                        },
                    },
                    "required": [],
                },
            )
        ),
        FunctionToolDefinition(
            function=FunctionDefinition(
                name="search_components",
                description="Search for architecture components in IcePanel by keyword or ID. Searches component names and descriptions across microservices, libraries, gateways. Returns matching components with deep links.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search keyword or component ID (e.g., 'authentication', 'COMP-201')",
                        },
                    },
                    "required": ["query"],
                },
            )
        ),
        FunctionToolDefinition(
            function=FunctionDefinition(
                name="get_component",
                description="Retrieve a specific architecture component by ID from IcePanel. Returns full component details including name, type, technology, relationships, and deep link.",
                parameters={
                    "type": "object",
                    "properties": {
                        "component_id": {
                            "type": "string",
                            "description": "The component ID (e.g., 'COMP-201')",
                        },
                    },
                    "required": ["component_id"],
                },
            )
        ),
        FunctionToolDefinition(
            function=FunctionDefinition(
                name="list_related_artifacts",
                description="List all artifacts related to a given requirement, work item, component, or test. Traverses relationships to find connected artifacts across systems. Returns 1-hop neighbors with IDs, titles, and deep links.",
                parameters={
                    "type": "object",
                    "properties": {
                        "artifact_id": {
                            "type": "string",
                            "description": "The artifact ID (e.g., 'REQ-001', 'WI-101', 'COMP-201')",
                        },
                    },
                    "required": ["artifact_id"],
                },
            )
        ),
    ]


# Tool function mapping for execution
TOOL_FUNCTIONS = {
    "search_requirements": search_requirements,
    "get_requirement": get_requirement,
    "list_related_requirements": list_related_requirements,
    "find_requirements_by_work_item": find_requirements_by_work_item,
    "search_work_items": search_work_items,
    "get_work_item": get_work_item,
    "get_my_work_items": get_my_work_items,
    "search_components": search_components,
    "get_component": get_component,
    "list_related_artifacts": list_related_artifacts,
}
