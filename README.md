# azure-mcp-agent-starter

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/RajAnandakumar-msft/azure-mcp-agent-starter/actions/workflows/tests.yml/badge.svg)](https://github.com/RajAnandakumar-msft/azure-mcp-agent-starter/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A starter kit for building Azure AI Foundry agents that connect to **multiple MCP servers simultaneously** — with config-driven server registration, per-server authentication, and read-only safety enforcement built in.

Clone it, fill in your `.env`, and have a working multi-server agent running in under 10 minutes.

---

## What this kit gives you

| Feature | Description |
|---|---|
| Config-driven servers | Add/remove MCP servers by editing `mcp_servers.yaml` — no code changes |
| Per-server auth | API key, PAT, OAuth stub, or anonymous — declared per-server in YAML |
| Read-only guardrails | Registry blocks write-prefixed tool calls before they reach any server |
| Response normalization | Consistent envelope across heterogeneous MCP server responses |
| Demo MCP server | Azure Functions app with JAMA + IcePanel fixture data to run locally |
| 100+ tests | Full coverage of auth providers, registry, normalizer, and MCP protocol |

---

## Architecture

```
User  ──►  main.py  ──►  AgentsClient (Azure AI Foundry)
                               │
                          tools.py  (agent tool definitions)
                               │
                        ServerRegistry  (mcp_servers.yaml)
                               │
                     AuthProvider  (per-server auth)
                               │
                          MCP server  (HTTP / stdio)
                               │
                          Normalizer  (standard envelope)
                               │
                          ◄── response with deep links
```

The `ServerRegistry` reads `mcp_servers.yaml` at startup. Add a new server by adding a YAML entry — no Python changes required.

---

## Quick start

> Full details in [QUICKSTART.md](QUICKSTART.md).

**Prerequisites:**

| Tool | Version | Why |
|---|---|---|
| Python | 3.10+ | Agent runtime |
| Azure CLI | latest | `az login` for Foundry auth |
| Node.js + Azure Functions Core Tools | 18+ / v4 | Run demo MCP server locally |
| Azure AI Foundry project | — | Deployed agent required |

**Steps:**

```bash
# 1. Clone and install
git clone https://github.com/RajAnandakumar-msft/azure-mcp-agent-starter.git
cd azure-mcp-agent-starter/agent_app
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# fill in AZURE_EXISTING_AIPROJECT_ENDPOINT and AZURE_EXISTING_AGENT_ID

# 3. Log in
az login

# 4. Start the demo MCP server (separate terminal)
cd ../demo_mcp_server
func start --port 7070

# 5. Run the agent
python -m agent_app.main
```

Try asking:
- `show me authentication requirements`
- `what's related to REQ-001?`
- `find architecture components tagged with "API Gateway"`

---

## Adding your own MCP server (4 steps, no code)

**1.** Add an entry to `mcp_servers.yaml`:

```yaml
servers:
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

**2.** Add the variable to `.env`:
```
MY_SYSTEM_KEY=your-key
```

**3.** Add a tool in `agent_app/tools.py`:
```python
@ai_function
async def search_my_system(query: str) -> str:
    """Search my system for artifacts matching query."""
    client = get_mcp_client("my_system")
    return await client.call_tool("search", {"q": query})
```

**4.** Restart the agent. The new server is registered automatically.

See [examples/README.md](examples/README.md) for auth recipes, stdio servers, and response normalization.

---

## Repository layout

```
azure-mcp-agent-starter/
├── .github/
│   └── copilot-instructions.md    # Copilot rules (single source of truth)
├── agent_app/                      # Main agent application
│   ├── auth/                       # AuthProvider protocol + 4 implementations
│   ├── registry/                   # Config-driven ServerRegistry
│   ├── normalization/              # Response envelope normalizer
│   ├── tests/                      # 100+ unit tests
│   ├── config.py                   # Environment loading & typed config
│   ├── main.py                     # Agent run loop (entry point)
│   ├── tools.py                    # Agent tool definitions
│   ├── mcp_client.py               # JSON-RPC 2.0 HTTP + stdio clients
│   └── mcp_utils.py                # Parallel MCP fetch utilities
├── demo_mcp_server/                # Azure Functions demo MCP server
│   ├── function_app.py             # MCP endpoint (JAMA + IcePanel demo data)
│   ├── demo_data.py                # Demo fixtures
│   └── mcp_response.py             # Standard response envelope helper
├── tests/                          # Integration tests (MCP protocol + endpoint)
├── examples/                       # Guides for extending the kit
│   ├── README.md                   # Extension guide
│   ├── auth_patterns.md            # Auth recipe examples
│   └── custom_http_server/README.md
├── mcp_servers.yaml                # Server registry (edit to add/remove servers)
├── .env.example                    # Environment variable template
├── QUICKSTART.md                   # 10-minute setup guide
├── ruff.toml                       # Linter / formatter config
└── README.md                       # This file
```

---

## Running tests

```bash
pytest agent_app/tests/ -v
```

```bash
pytest tests/ -v          # MCP protocol + endpoint integration tests
```

---

## Key design decisions

| Decision | Choice | Rationale |
|---|---|---|
| Agent client | `AzureOpenAIResponsesClient` | Modern Responses API — preferred over Chat Completions |
| AI platform | Azure AI Foundry | Multi-provider models, project-scoped management |
| MCP host | Azure Functions | Simplest demo endpoint; Container Apps as fallback |
| Data layer | JSON fixtures | Start simple; migrate to Blob/Cosmos when volume requires it |
| Live APIs | Demo datasets only | Prevents real tenant dependencies in a starter kit |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)

