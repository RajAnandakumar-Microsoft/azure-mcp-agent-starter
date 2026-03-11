"""Test MCP protocol compliance.

Tests JSON-RPC 2.0 protocol and MCP response formats for all three servers.
"""

import json
import sys
from pathlib import Path

# Add demo_mcp_server to path
sys.path.insert(0, str(Path(__file__).parent.parent / "demo_mcp_server"))

from mcp_protocol import (
    MCPError,
    create_jsonrpc_error,
    create_jsonrpc_response,
    create_mcp_content,
    create_tool_definition,
    parse_jsonrpc_request,
)


def test_parse_jsonrpc_request():
    """Test JSON-RPC request parsing."""
    print("Testing parse_jsonrpc_request...")

    # Valid request
    request_body = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        }
    )
    request_id, method, params = parse_jsonrpc_request(request_body)
    assert request_id == 1
    assert method == "tools/list"
    assert params == {}
    print("  ✓ Valid request parsed correctly")

    # Invalid JSON
    try:
        parse_jsonrpc_request("not json")
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "Invalid JSON" in str(e) or "Parse error" in str(e)
        print("  ✓ Invalid JSON rejected")

    # Missing jsonrpc field
    try:
        request_body = json.dumps({"id": 1, "method": "test"})
        parse_jsonrpc_request(request_body)
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "Invalid request" in str(e) or "Invalid Request" in str(e)
        print("  ✓ Missing jsonrpc field rejected")

    # Invalid jsonrpc version
    try:
        request_body = json.dumps(
            {"jsonrpc": "1.0", "id": 1, "method": "test"}
        )
        parse_jsonrpc_request(request_body)
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "Invalid request" in str(e) or "Invalid Request" in str(e)
        print("  ✓ Invalid jsonrpc version rejected")

    print()


def test_jsonrpc_response():
    """Test JSON-RPC response creation."""
    print("Testing JSON-RPC responses...")

    # Success response
    response = create_jsonrpc_response(1, {"status": "ok"})
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    assert response["result"]["status"] == "ok"
    print("  ✓ Success response created correctly")

    # Error response
    response = create_jsonrpc_error(
        1, MCPError.INVALID_PARAMS, "Missing param"
    )
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    assert response["error"]["code"] == MCPError.INVALID_PARAMS
    assert response["error"]["message"] == "Missing param"
    print("  ✓ Error response created correctly")

    print()


def test_mcp_content():
    """Test MCP content creation."""
    print("Testing MCP content...")

    content = create_mcp_content("text", text="Hello", mimeType="text/plain")
    assert content["type"] == "text"
    assert content["text"] == "Hello"
    assert content["mimeType"] == "text/plain"
    print("  ✓ MCP content created correctly")

    data = {"key": "value"}
    content = create_mcp_content(
        "text", text=json.dumps(data), mimeType="application/json"
    )
    assert json.loads(content["text"]) == data
    print("  ✓ JSON content created correctly")

    print()


def test_tool_definition():
    """Test tool definition creation."""
    print("Testing tool definitions...")

    tool_def = create_tool_definition(
        name="test_tool",
        description="A test tool",
        input_schema={
            "type": "object",
            "properties": {"param": {"type": "string"}},
            "required": ["param"],
        },
    )

    assert tool_def["name"] == "test_tool"
    assert tool_def["description"] == "A test tool"
    assert tool_def["inputSchema"]["type"] == "object"
    assert "param" in tool_def["inputSchema"]["properties"]
    print("  ✓ Tool definition created correctly")

    print()


def test_mcp_error_codes():
    """Test MCP error codes."""
    print("Testing MCP error codes...")

    assert MCPError.PARSE_ERROR == -32700
    assert MCPError.INVALID_REQUEST == -32600
    assert MCPError.METHOD_NOT_FOUND == -32601
    assert MCPError.INVALID_PARAMS == -32602
    assert MCPError.INTERNAL_ERROR == -32603
    print("  ✓ All error codes defined correctly")

    print()


if __name__ == "__main__":
    print("=" * 60)
    print("MCP Protocol Compliance Tests")
    print("=" * 60)
    print()

    test_parse_jsonrpc_request()
    test_jsonrpc_response()
    test_mcp_content()
    test_tool_definition()
    test_mcp_error_codes()

    print("=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
