"""MCP Protocol implementation helpers.

Provides JSON-RPC 2.0 handling for MCP server endpoints.
"""

import json
from typing import Any


class MCPError(Exception):
    """Custom exception for MCP protocol errors.
    
    Allows raising errors that will be formatted as JSON-RPC error responses.
    """

    def __init__(self, code: int, message: str, data: Any = None):
        """Initialize MCP error.
        
        Args:
            code: JSON-RPC error code
            message: Error message
            data: Additional error data
        """
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)
    
    # JSON-RPC 2.0 error codes
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603


def create_jsonrpc_error(
    id: str | int | None, code: int, message: str, data: Any = None
) -> dict[str, Any]:
    """Create JSON-RPC 2.0 error response.

    Args:
        id: Request ID (null for notification errors)
        code: Error code
        message: Error message
        data: Additional error data

    Returns:
        JSON-RPC error response
    """
    error = {"code": code, "message": message}
    if data is not None:
        error["data"] = data

    return {"jsonrpc": "2.0", "id": id, "error": error}


def create_jsonrpc_response(id: str | int, result: Any) -> dict[str, Any]:
    """Create JSON-RPC 2.0 success response.

    Args:
        id: Request ID
        result: Result data

    Returns:
        JSON-RPC success response
    """
    return {"jsonrpc": "2.0", "id": id, "result": result}


def parse_jsonrpc_request(body: str | dict) -> tuple[str | int | None, str, dict]:
    """Parse JSON-RPC 2.0 request.

    Args:
        body: Request body (JSON string or dict)

    Returns:
        Tuple of (id, method, params)

    Raises:
        ValueError: If request is invalid
    """
    try:
        if isinstance(body, str):
            data = json.loads(body)
        else:
            data = body

        # Validate JSON-RPC 2.0
        if data.get("jsonrpc") != "2.0":
            raise ValueError("Missing or invalid jsonrpc field")

        request_id = data.get("id")
        method = data.get("method")
        params = data.get("params", {})

        if not method:
            raise ValueError("Missing method field")

        return request_id, method, params

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")
    except Exception as e:
        raise ValueError(f"Invalid request: {e}")


def create_tool_definition(
    name: str,
    description: str,
    input_schema: dict[str, Any],
) -> dict[str, Any]:
    """Create MCP tool definition.

    Args:
        name: Tool name
        description: Tool description
        input_schema: JSON Schema for tool parameters

    Returns:
        MCP tool definition
    """
    return {
        "name": name,
        "description": description,
        "inputSchema": input_schema,
    }


def create_mcp_content(type: str, text: str | None = None, **kwargs) -> dict[str, Any]:
    """Create MCP content object.

    Args:
        type: Content type (text, image, resource)
        text: Text content
        **kwargs: Additional content fields

    Returns:
        MCP content object
    """
    content = {"type": type}
    if text is not None:
        content["text"] = text
    content.update(kwargs)
    return content
