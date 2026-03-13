# Demo MCP Server

Single unified Azure Function that provides MCP-compliant tools for both JAMA requirements and IcePanel architecture components.

## Features

- **Single endpoint**: One server handles both JAMA and IcePanel tools
- **Port 7070**: Replaces the previous separate servers on ports 7071 and 7073
- **MCP compliant**: Full JSON-RPC 2.0 protocol implementation
- **Shared demo data**: Centralized `demo_data.py` with all fixtures

## Available Tools

### JAMA Requirements
- `search_requirements` - Search by keyword or ID
- `get_requirement` - Get specific requirement details

### IcePanel Components
- `search_components` - Search architecture components
- `get_component` - Get specific component details

## Running Locally

```powershell
cd demo_mcp_server
func start --port 7070
```

## Testing

```powershell
# List all available tools
Invoke-RestMethod -Uri "http://localhost:7070/api/mcp" -Method Post -Body (@{
    jsonrpc = "2.0"
    id = 1
    method = "tools/list"
    params = @{}
} | ConvertTo-Json) -ContentType "application/json"

# Search requirements
Invoke-RestMethod -Uri "http://localhost:7070/api/mcp" -Method Post -Body (@{
    jsonrpc = "2.0"
    id = 2
    method = "tools/call"
    params = @{
        name = "search_requirements"
        arguments = @{ query = "authentication" }
    }
} | ConvertTo-Json) -ContentType "application/json"

# Search components
Invoke-RestMethod -Uri "http://localhost:7070/api/mcp" -Method Post -Body (@{
    jsonrpc = "2.0"
    id = 3
    method = "tools/call"
    params = @{
        name = "search_components"
        arguments = @{ query = "API Gateway" }
    }
} | ConvertTo-Json) -ContentType "application/json"
```

## Architecture

```
demo_mcp_server/
├── function_app.py      # Unified MCP endpoint
├── demo_data.py         # Demo requirements & components
├── mcp_protocol.py      # JSON-RPC protocol helpers
├── mcp_response.py      # MCP response formatters
├── host.json            # Azure Functions config
├── requirements.txt     # Python dependencies
└── local.settings.json  # Local development settings
```

## Deployment

```powershell
# Deploy to Azure (when ready)
$resourceGroup = "mcp-agent-rg"
$location = "eastus"
$appName = "mcp-demo-server"

az functionapp create `
  --resource-group $resourceGroup `
  --consumption-plan-location $location `
  --runtime python `
  --runtime-version 3.11 `
  --functions-version 4 `
  --name $appName `
  --storage-account mcpdemostorage `
  --os-type Linux

func azure functionapp publish $appName
```
