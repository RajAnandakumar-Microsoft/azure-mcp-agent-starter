"""Unified Demo MCP Server - JAMA and IcePanel capabilities.

Single Azure Function app that provides MCP-compliant tools for both
JAMA requirements and IcePanel architecture components.
"""

import json
import logging
import azure.functions as func

from mcp_protocol import (
    MCPError,
    create_jsonrpc_error,
    create_jsonrpc_response,
    create_mcp_content,
    create_tool_definition,
    parse_jsonrpc_request,
)
from mcp_response import create_mcp_response, create_search_response
from demo_data import DEMO_REQUIREMENTS, DEMO_COMPONENTS

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Tool Definitions
# ============================================================================

TOOLS = [
    # JAMA Requirements Tools
    create_tool_definition(
        name="search_requirements",
        description="Search for requirements in JAMA by keyword or ID. Returns matching requirements with IDs, titles, statuses, priorities, and deep links.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keyword or requirement ID (e.g., 'authentication', 'REQ-001')",
                }
            },
            "required": ["query"],
        },
    ),
    create_tool_definition(
        name="get_requirement",
        description="Retrieve a specific requirement by ID from JAMA. Returns full requirement details including title, description, status, priority, relationships, and deep link.",
        input_schema={
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Requirement ID (e.g., 'REQ-001')",
                }
            },
            "required": ["id"],
        },
    ),
    create_tool_definition(
        name="list_related_requirements",
        description="List all artifacts related to a JAMA requirement. Returns work items, components, and other requirements linked to the specified requirement ID.",
        input_schema={
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Requirement ID (e.g., 'REQ-001')",
                }
            },
            "required": ["id"],
        },
    ),
    create_tool_definition(
        name="find_requirements_by_work_item",
        description="Find JAMA requirements that reference a specific Azure DevOps work item. Use this when you need to find which requirements are linked to a work item ID.",
        input_schema={
            "type": "object",
            "properties": {
                "work_item_id": {
                    "type": "string",
                    "description": "Work item ID with or without WI- prefix (e.g., '9', 'WI-9', '10')",
                }
            },
            "required": ["work_item_id"],
        },
    ),
    # IcePanel Components Tools
    create_tool_definition(
        name="search_components",
        description="Search for architecture components in IcePanel by keyword or ID. Searches component names and descriptions across microservices, libraries, gateways. Returns matching components with deep links.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keyword or component ID (e.g., 'authentication', 'COMP-201')",
                }
            },
            "required": ["query"],
        },
    ),
    create_tool_definition(
        name="get_component",
        description="Retrieve a specific architecture component by ID from IcePanel. Returns full component details including name, type, technology, relationships, and deep link.",
        input_schema={
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Component ID (e.g., 'COMP-201')",
                }
            },
            "required": ["id"],
        },
    ),
    create_tool_definition(
        name="list_related_components",
        description="List all artifacts related to an IcePanel component. Returns requirements, work items, and other components linked to the specified component ID.",
        input_schema={
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Component ID (e.g., 'COMP-201')",
                }
            },
            "required": ["id"],
        },
    ),
]


# ============================================================================
# Tool Implementation Functions
# ============================================================================


def search_requirements(query: str) -> dict:
    """Search JAMA requirements by keyword or ID."""
    query_lower = query.lower()
    matches = []

    for req in DEMO_REQUIREMENTS:
        if (
            query_lower in req["id"].lower()
            or query_lower in req["title"].lower()
            or query_lower in req["description"].lower()
        ):
            matches.append(req)

    return create_search_response(
        source_system="JAMA",
        artifact_type="requirement",
        query=query,
        results=matches,
    )


def get_requirement(requirement_id: str) -> dict:
    """Get a specific JAMA requirement by ID."""
    for req in DEMO_REQUIREMENTS:
        if req["id"].upper() == requirement_id.upper():
            return create_mcp_response(
                source_system="JAMA",
                artifact_type="requirement",
                stable_id=req["id"],
                title=req["title"],
                summary=req["description"],
                deeplink_url=req["deeplink_url"],
                data={
                    "status": req["status"],
                    "priority": req["priority"],
                    "category": req["category"],
                },
                related=req.get("related", []),
            )

    raise MCPError(
        code=-32602,
        message=f"Requirement not found: {id}",
        data={"available_ids": [r["id"] for r in DEMO_REQUIREMENTS]},
    )


def list_related_requirements(id: str) -> dict:
    """List all related artifacts for a JAMA requirement."""
    for req in DEMO_REQUIREMENTS:
        if req["id"].upper() == id.upper():
            return {
                "source_system": "JAMA",
                "artifact_id": req["id"],
                "artifact_type": "requirement",
                "related": req.get("related", []),
                "total_count": len(req.get("related", [])),
            }

    raise MCPError(
        code=-32602,
        message=f"Requirement not found: {id}",
        data={"available_ids": [r["id"] for r in DEMO_REQUIREMENTS]},
    )


def find_requirements_by_work_item(work_item_id: str) -> dict:
    """Find JAMA requirements that reference a specific work item ID."""
    # Normalize work item ID (remove WI- prefix if present)
    wi_id = work_item_id.upper().replace("WI-", "")
    
    matching_requirements = []
    
    for req in DEMO_REQUIREMENTS:
        # Check if this requirement has the work item in its related array
        related_items = req.get("related", [])
        for related in related_items:
            if (related.get("type") == "work_item" and 
                related.get("system") == "ADO" and 
                related.get("id") == wi_id):
                matching_requirements.append({
                    "id": req["id"],
                    "title": req["title"],
                    "status": req["status"],
                    "priority": req["priority"],
                    "category": req["category"],
                    "deeplink_url": req["deeplink_url"],
                })
                break  # Don't add the same requirement twice
    
    return {
        "source_system": "JAMA",
        "query_type": "find_by_work_item",
        "work_item_id": work_item_id,
        "results": matching_requirements,
        "total_count": len(matching_requirements),
    }


def search_components(query: str) -> dict:
    """Search IcePanel components by keyword or ID."""
    query_lower = query.lower()
    matches = []

    for comp in DEMO_COMPONENTS:
        if (
            query_lower in comp["id"].lower()
            or query_lower in comp["name"].lower()
            or query_lower in comp["description"].lower()
            or query_lower in comp["technology"].lower()
        ):
            matches.append(comp)

    return create_search_response(
        source_system="IcePanel",
        artifact_type="component",
        query=query,
        results=matches,
    )


def get_component(id: str) -> dict:
    """Get a specific IcePanel component by ID."""
    for comp in DEMO_COMPONENTS:
        if comp["id"].upper() == id.upper():
            return create_mcp_response(
                source_system="IcePanel",
                artifact_type="component",
                stable_id=comp["id"],
                title=comp["name"],
                summary=comp["description"],
                deeplink_url=comp["deeplink_url"],
                data={
                    "type": comp["type"],
                    "technology": comp["technology"],
                    "layer": comp["layer"],
                },
                related=comp.get("related", []),
            )

    raise MCPError(
        code=-32602,
        message=f"Component not found: {id}",
        data={"available_ids": [c["id"] for c in DEMO_COMPONENTS]},
    )


def list_related_components(id: str) -> dict:
    """List all related artifacts for an IcePanel component."""
    for comp in DEMO_COMPONENTS:
        if comp["id"].upper() == id.upper():
            return {
                "source_system": "IcePanel",
                "artifact_id": comp["id"],
                "artifact_type": "component",
                "related": comp.get("related", []),
                "total_count": len(comp.get("related", [])),
            }

    raise MCPError(
        code=-32602,
        message=f"Component not found: {id}",
        data={"available_ids": [c["id"] for c in DEMO_COMPONENTS]},
    )


# ============================================================================
# Tool Dispatcher
# ============================================================================

TOOL_HANDLERS = {
    "search_requirements": search_requirements,
    "get_requirement": get_requirement,
    "list_related_requirements": list_related_requirements,
    "find_requirements_by_work_item": find_requirements_by_work_item,
    "search_components": search_components,
    "get_component": get_component,
    "list_related_components": list_related_components,
}


def handle_tool_call(tool_name: str, arguments: dict) -> dict:
    """Route tool calls to appropriate handler."""
    if tool_name not in TOOL_HANDLERS:
        raise MCPError(
            code=-32602,
            message=f"Tool not found: {tool_name}",
            data={"available_tools": list(TOOL_HANDLERS.keys())},
        )

    handler = TOOL_HANDLERS[tool_name]
    return handler(**arguments)


# ============================================================================
# MCP Endpoint
# ============================================================================


@app.route(route="mcp", methods=["POST"])
def mcp_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """Unified MCP endpoint for all demo tools."""
    try:
        # Parse JSON-RPC request
        try:
            body = req.get_json()
        except ValueError as e:
            return func.HttpResponse(
                json.dumps(
                    create_jsonrpc_error(
                        request_id=None,
                        code=-32700,
                        message="Parse error: Invalid JSON",
                        data={"error": str(e)},
                    )
                ),
                mimetype="application/json",
                status_code=400,
            )

        # Unpack tuple from parse_jsonrpc_request
        request_id, method, params = parse_jsonrpc_request(body)

        logger.info(f"MCP request: {method} with params: {params}")

        # Route to appropriate handler
        if method == "tools/list":
            result = {"tools": TOOLS}
            response = create_jsonrpc_response(request_id, result)

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if not tool_name:
                raise MCPError(
                    code=-32602,
                    message="Missing required parameter: name",
                    data={"params": params},
                )

            # Call the tool
            tool_result = handle_tool_call(tool_name, arguments)

            # Wrap in MCP content format (text type with JSON result)
            result = {"content": [create_mcp_content("text", text=json.dumps(tool_result))]}
            response = create_jsonrpc_response(request_id, result)

        else:
            raise MCPError(
                code=-32601,
                message=f"Method not found: {method}",
                data={"supported_methods": ["tools/list", "tools/call"]},
            )

        return func.HttpResponse(
            json.dumps(response), mimetype="application/json", status_code=200
        )

    except MCPError as e:
        logger.error(f"MCP error: {e.message}")
        error_response = create_jsonrpc_error(
            id=request_id if "request_id" in locals() else None,
            code=e.code,
            message=e.message,
            data=e.data,
        )
        return func.HttpResponse(
            json.dumps(error_response), mimetype="application/json", status_code=400
        )

    except Exception as e:
        logger.exception("Unexpected error in MCP endpoint")
        error_response = create_jsonrpc_error(
            id=request_id if "request_id" in locals() else None,
            code=-32603,
            message="Internal error",
            data={"error": str(e)},
        )
        return func.HttpResponse(
            json.dumps(error_response), mimetype="application/json", status_code=500
        )
