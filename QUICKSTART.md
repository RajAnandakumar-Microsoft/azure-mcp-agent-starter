# Quick Start

Get the agent running locally in ~10 minutes.

---

## Prerequisites

- Python 3.10+
- Azure CLI (`az`) — for Azure AI Foundry authentication
- Node.js 18+ — only if using the Azure DevOps MCP server
- An Azure AI Foundry project with an agent deployed

---

## 1. Install dependencies

```bash
cd agent_app
pip install -r requirements.txt
```

---

## 2. Configure environment

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

Minimum required values:

```env
# Azure AI Foundry
AZURE_EXISTING_AIPROJECT_ENDPOINT=https://<account>.services.ai.azure.com/api/projects/<project>
AZURE_EXISTING_AGENT_ID=<your-agent-id>

# Demo MCP server (start demo_mcp_server/ locally via func start)
MCP_DEMO_URL=http://localhost:7070/api

# Azure DevOps MCP (optional — skip if not using ADO)
ADO_MCP_PATH=/path/to/@microsoft/mcp-server-azuredevops/dist/index.js
ADO_ORG=your-org-name
ADO_MCP_AUTH_TOKEN=your-ado-pat
```

---

## 3. Log in to Azure

```bash
az login
```

If using a specific tenant:
```bash
az login --tenant <tenant-id>
```

---

## 4. Start the demo MCP server (optional)

The demo server provides JAMA and IcePanel tools with fixture data.

```bash
cd demo_mcp_server
func start --port 7070
```

---

## 5. Run the agent

```bash
python -m agent_app.main
```

Example queries to try:
- `show me requirements related to authentication`
- `what work items are assigned to me?`
- `find architecture components tagged with "API Gateway"`
- `what's related to REQ-001?`

---

## Adding a new MCP server

**No code changes required.** Edit `mcp_servers.yaml`:

```yaml
servers:
  # ... existing entries ...

  - label: my_system
    description: "My system"
    transport: http
    url: "${MY_SYSTEM_URL:-http://localhost:7071/api}"
    auth:
      type: api_key
      header: "x-functions-key"
      env_var: MY_SYSTEM_KEY
    read_only: true
```

Then add to `.env`:
```
MY_SYSTEM_KEY=your-function-key
```

Restart the agent — the new server is available immediately.

See `examples/README.md` for the full guide, including:
- stdio servers (for official MCP servers like ADO, GitHub)
- auth recipes (API key, PAT, multi-tenant)
- response normalization for non-standard schemas

---

## Configuring auth per server

Each server entry in `mcp_servers.yaml` has an independent `auth:` block.

| Auth type | When to use |
|-----------|-------------|
| `none` | Local dev / anonymous servers |
| `api_key` | Azure Functions with function keys |
| `pat` | Azure DevOps, GitHub, Jira PATs |
| `oauth` | Azure AD delegated auth (see `examples/auth_patterns.md`) |

See `examples/auth_patterns.md` for complete recipes with copy-paste config.

---

## Project layout

```
mcp_servers.yaml        ← Server registry: add new servers here
agent_app/
  auth/                 ← Per-server auth providers (api_key, pat, oauth, none)
  registry/             ← ServerRegistry: loads YAML, creates clients
  normalization/        ← Response normalization to standard envelope
  config.py             ← Azure AI Foundry + legacy MCP config
  mcp_client.py         ← MCPClient (HTTP) + StdioMCPClient + get_mcp_client()
  tools.py              ← Agent tool definitions (registered with Azure AI agent)
  main.py               ← CLI entry point
demo_mcp_server/        ← Working example: HTTP MCP server (JAMA + IcePanel demo)
examples/               ← Templates and recipes for extending the kit
```

---

## Running tests

```bash
cd tests
pytest
```

Coverage report is written to `htmlcov/index.html`.
