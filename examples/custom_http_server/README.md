# Custom HTTP MCP Server Template

This template shows the minimum structure for a new HTTP MCP server
(Azure Functions) that integrates with the starter kit.

Use `demo_mcp_server/` at the repo root as a full working reference.

---

## Files

```
custom_http_server/
├── function_app.py      ← Azure Function + MCP tool handlers
├── mcp_response.py      ← Copy from demo_mcp_server/ (standard envelope)
├── mcp_protocol.py      ← Copy from demo_mcp_server/ (JSON-RPC helpers)
├── host.json            ← Azure Functions host config
├── local.settings.json  ← Local dev settings (add to .gitignore)
└── requirements.txt     ← azure-functions, mcp
```

---

## Minimal function_app.py skeleton

```python
import json
import logging
import azure.functions as func
from mcp_protocol import create_jsonrpc_response, create_mcp_content, parse_jsonrpc_request
from mcp_response import create_mcp_response

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
logger = logging.getLogger(__name__)

TOOLS = [
    {
        "name": "get_item",
        "description": "Retrieve an item by ID from My System.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "Item ID"}
            },
            "required": ["item_id"],
        },
    }
]

@app.route(route="mcp", methods=["POST"])
def mcp_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_body().decode()
        request_id, method, params = parse_jsonrpc_request(body)

        if method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            result = handle_tool_call(params)
        else:
            return func.HttpResponse(status_code=404)

        response = create_jsonrpc_response(request_id, result)
        return func.HttpResponse(json.dumps(response), mimetype="application/json")
    except Exception as e:
        logger.exception("MCP endpoint error")
        return func.HttpResponse(str(e), status_code=500)


def handle_tool_call(params: dict) -> dict:
    tool_name = params.get("name")
    args = params.get("arguments", {})

    if tool_name == "get_item":
        item_id = args.get("item_id", "")
        # Replace with real data lookup
        result = create_mcp_response(
            source_system="My System",
            artifact_type="item",
            stable_id=item_id,
            title=f"Item {item_id}",
            summary="A sample item.",
            deeplink_url=f"https://my-system.example.com/items/{item_id}",
        )
        return {"content": [{"type": "text", "text": json.dumps(result)}]}

    return {"isError": True, "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]}
```

---

## Registering in mcp_servers.yaml

```yaml
- label: my_system
  description: "My custom system"
  transport: http
  url: "${MY_SYSTEM_URL:-http://localhost:7071/api}"
  auth:
    type: api_key
    header: "x-functions-key"
    env_var: MY_SYSTEM_FUNCTION_KEY
  read_only: true
```

---

## Response envelope contract

Every tool response MUST include these fields so the agent can surface deep links:

| Field | Required | Description |
|-------|----------|-------------|
| `source_system` | Yes | Human-readable system name |
| `artifact_type` | Yes | Type of artifact (e.g., "item", "ticket") |
| `stable_id` | Yes | Unique, stable identifier |
| `title` | Yes | Short display title |
| `summary` | Recommended | 1-3 sentence description |
| `deeplink_url` | Yes | Clickable URL to the artifact |
| `related` | Recommended | Array of related artifact refs |
