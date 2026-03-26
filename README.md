# azure-mcp-agent-starter

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/RajAnandakumar-Microsoft/azure-mcp-agent-starter/actions/workflows/tests.yml/badge.svg)](https://github.com/RajAnandakumar-Microsoft/azure-mcp-agent-starter/actions/workflows/tests.yml)
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

```mermaid
flowchart LR
    U(["👤 User"]):::user -->|"chat query"| MAIN["main.py\nAgent Loop"]:::agent

    subgraph FOUNDRY ["Azure AI Foundry"]
        MAIN -->|"user prompt +\ntool definitions"| LLM["LLM\n(Responses API)"]:::llm
        LLM -->|"tool_calls[]"| MAIN
    end

    MAIN -->|"dispatch by\nfunction name"| TOOLS["tools.py\nTOOL_FUNCTIONS"]:::tools

    subgraph REGISTRY ["Server Registry"]
        direction TB
        TOOLS -->|"get_mcp_client(label)"| REG["ServerRegistry\nmcp_servers.yaml"]:::registry
        REG -->|"build provider"| AUTH["Auth Provider\n(API Key / PAT / OAuth)"]:::auth
    end

    subgraph MCP_SERVERS ["MCP Servers"]
        direction TB
        AUTH -->|"HTTP + headers"| HTTP_MCP["HTTP MCP Server\n(Azure Functions)"]:::mcp
        AUTH -->|"stdio + env vars"| STDIO_MCP["Stdio MCP Server\n(subprocess)"]:::mcp
    end

    HTTP_MCP -->|"JSON-RPC response"| NORM["Normalizer\n(standard envelope)"]:::norm
    STDIO_MCP -->|"JSON-RPC response"| NORM
    NORM -->|"normalized result"| MAIN
    MAIN -->|"answer +\ndeep links"| U

    classDef user fill:#E8F5E9,stroke:#388E3C,color:#1B5E20
    classDef agent fill:#E3F2FD,stroke:#1565C0,color:#0D47A1
    classDef llm fill:#FFF3E0,stroke:#EF6C00,color:#BF360C
    classDef tools fill:#F3E5F5,stroke:#7B1FA2,color:#4A148C
    classDef registry fill:#FFF9C4,stroke:#F9A825,color:#F57F17
    classDef auth fill:#FFECB3,stroke:#FFA000,color:#E65100
    classDef mcp fill:#E0F7FA,stroke:#00838F,color:#006064
    classDef norm fill:#FCE4EC,stroke:#C62828,color:#B71C1C
```

The `ServerRegistry` reads `mcp_servers.yaml` at startup and wires up per-server authentication automatically. Add a new server by adding a YAML entry — no Python changes required.

---

## Quick start

> Full details in [QUICKSTART.md](QUICKSTART.md).

**Prerequisites:**

| Tool | Version | Why |
|---|---|---|
| Python | 3.10+ | Agent runtime |
| Azure CLI | latest | `az login` for Foundry auth |
| Node.js + [Azure Functions Core Tools](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local) | 18+ / v4 | Run demo MCP server locally |
| Azure AI Foundry project | — | Deployed agent required |

**Steps:**

```bash
# 1. Clone and install
git clone https://github.com/RajAnandakumar-Microsoft/azure-mcp-agent-starter.git
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

