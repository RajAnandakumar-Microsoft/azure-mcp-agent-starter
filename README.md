# Olympus Traceability Agent - Proof of Concept

This repository demonstrates cross-system traceability using Azure AI Foundry Agent Service, the Microsoft Agent Framework, and the Model Context Protocol (MCP). The agent navigates and links artifacts across requirements management (JAMA), work items (Azure DevOps), and architecture (IcePanel) systems.

## Current Status

**Phase 1: Agent with Local Tools (✅ Complete)**
- Azure AI Foundry Agent Service integration
- Multi-turn conversation support
- 7 read-only tools for search/get/relationships
- Environment-based configuration

**Phase 2: MCP Protocol Servers (✅ Complete)**
- Three MCP servers (JAMA, ADO, IcePanel) as Azure Functions
- JSON-RPC 2.0 protocol implementation
- Demo datasets with cross-system relationships
- Deep-linking for all artifacts
- Single unified demo server on port 7070 (JAMA + IcePanel)
- ADO MCP: stdio connection to official Microsoft Azure DevOps MCP server

**Phase 3: Cloud Data Layer (⏳ Next)**
- Move demo data to Azure Blob Storage or Cosmos DB
- Deploy MCP servers to Azure Functions
- Production-ready data access patterns

## Repository Structure

```
v2/
├── .github/
│   └── copilot-instructions.md   # Copilot behavior rules (single source of truth)
├── agent_app/                     # Main agent application
│   ├── config.py                  # Environment loading & typed config
│   ├── main.py                    # Entry point & agent run loop
│   ├── tools.py                   # Agent tool definitions (calls MCP servers)
│   ├── mcp_client.py              # JSON-RPC 2.0 MCP client
│   ├── requirements.txt           # Python dependencies
│   ├── venv/                      # Virtual environment
│   └── tests/                     # Agent tests
├── mcp_servers/                   # MCP protocol servers
│   ├── shared_data.py             # Demo datasets (JAMA, ADO, IcePanel)
│   ├── mcp_protocol.py            # JSON-RPC 2.0 utilities
│   ├── mcp_response.py            # MCP response formatting
│   ├── jama_mcp/                  # JAMA MCP server (port 7071)
│   │   ├── function_app.py        # Azure Function with MCP endpoint
│   │   ├── host.json
│   │   ├── local.settings.json
│   │   └── requirements.txt
│   ├── (ado_mcp removed - using official Microsoft ADO MCP via stdio)
│   │   └── (same structure)
│   └── icepanel_mcp/              # IcePanel MCP server (port 7073)
│       └── (same structure)
├── ARCHITECTURE.md                # Complete data flow diagram
├── MCP_IMPLEMENTATION.md          # MCP protocol documentation
├── test_mcp_protocol.py           # MCP protocol compliance tests
├── test_mcp_endpoint.py           # Endpoint testing script
├── .env.example                   # Environment variable template
├── pytest.ini                     # Pytest configuration
├── ruff.toml                      # Ruff linter/formatter config
└── README.md                      # This file
```

## Quick Start

### Prerequisites
- Python 3.11+
- Azure CLI (`az login` for authentication)
- Azure Functions Core Tools (`npm install -g azure-functions-core-tools@4`)
- Azure AI Foundry project with deployed agent

### Setup

**1. Install Agent Dependencies**
```powershell
cd agent_app
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**2. Configure Environment**
```powershell
cp .env.example .env
# Edit .env with your Azure AI Foundry credentials:
# - AZURE_PROJECT_ENDPOINT
# - AZURE_AGENT_ID
```

**3. Start MCP Servers (3 terminals)**

Terminal 1 - JAMA MCP:
```powershell
cd mcp_servers\jama_mcp
func start --port 7071
```

Terminal 2 - ADO MCP:
```powershell
# ADO MCP: No server to start - uses stdio to official Microsoft MCP
# (Auto-started by agent when needed)
```

Terminal 3 - IcePanel MCP:
```powershell
cd mcp_servers\icepanel_mcp
func start --port 7073
```

**4. Run the Agent (4th terminal)**
```powershell
cd agent_app
.\venv\Scripts\Activate.ps1
cd ..
python -m agent_app.main
```

### Test Queries

Try these to see the cross-system traceability in action:

- `Search for authentication requirements`
- `Get details for REQ-001`
- `What are the related artifacts for REQ-001?` ← **Shows the magic!**
- `Find work items assigned to Jane Smith`
- `Search for OAuth work items`
- `Find authentication components`

See [ARCHITECTURE.md](ARCHITECTURE.md) for complete data flow diagrams.

## Development Standards

This PoC follows strict standards defined in [.github/copilot-instructions.md](.github/copilot-instructions.md):

- **Language:** Python 3.10+
- **Framework:** Microsoft Agent Framework
- **Client:** `AzureOpenAIResponsesClient` (Responses API)
- **Authentication:** Azure AD preferred; API key for demos
- **Type Safety:** All functions must include type hints
- **Formatting:** Ruff (88 char line length)
- **Testing:** pytest with minimum 40% coverage for demos
- **Security:** No hardcoded secrets; use .env + Key Vault

## Architecture

**Current Implementation:**
```
User Question
    ↓
Azure AI Foundry Agent (Cloud)
    ↓
agent_app/tools.py (Local)
    ↓
agent_app/mcp_client.py (JSON-RPC 2.0)
    ↓
MCP Servers (Local Azure Functions)
  - Demo MCP (port 7070) - JAMA requirements & IcePanel components
  - ADO MCP (stdio) - Official Microsoft Azure DevOps MCP server
    ↓
mcp_servers/shared_data.py (Demo Data)
    ↓
Formatted Response with Deep Links
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed flow diagrams and [MCP_IMPLEMENTATION.md](MCP_IMPLEMENTATION.md) for MCP protocol documentation.

## Key Design Decisions

See [.github/copilot-instructions.md](.github/copilot-instructions.md) for full rationale.

- **Responses API over Chat Completions:** Modern, recommended path
- **Demo datasets only:** No customer SaaS API calls
- **Read-only tools:** Search/get/list/relationships only
- **Deep links required:** Every artifact must include a clickable link
- **Azure Functions for MCP:** Simplest demo endpoint hosting

## Contributing

1. Follow the standards in [.github/copilot-instructions.md](.github/copilot-instructions.md)
2. Run `ruff format .` before committing
3. Ensure tests pass: `pytest`
4. Maintain minimum 40% coverage for demo code

## License

Internal Microsoft / Customer PoC. Not for public distribution.
