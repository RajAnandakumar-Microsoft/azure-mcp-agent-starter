# Architecture Overviewtool
apidata
## System Components (Current)

```
┌──────────────────────────────┐
│          User Query          │
└───────────────┬──────────────┘
        │
        ▼
┌──────────────────────────────┐
│ Azure AI Foundry Agent       │
│ (Cloud)                      │
└───────────────┬──────────────┘
        │ tool call
        ▼
┌──────────────────────────────┐
│ agent_app/tools.py           │
│ (Local CLI)                  │
└───────────────┬──────────────┘
    ┌───────┴───────────────────────────────┐
    │                                       │
    │ HTTP JSON-RPC 2.0                     │ stdio JSON-RPC 2.0
    ▼                                       ▼
┌──────────────────────────────┐    ┌──────────────────────────────┐
│ Demo MCP Server              │    │ Official Microsoft ADO MCP   │
│ Azure Functions              │    │ Node.js subprocess           │
│ demo_mcp_server/function_app │    └──────────────┬───────────────┘
│ Port 7070                    │                   │ REST
└──────────────┬───────────────┘                   ▼
    ┌──────┴───────────┐           ┌──────────────────────────────┐
    │                  │           │ Azure DevOps API             │
    ▼                  ▼           └──────────────────────────────┘
┌───────────────────┐  ┌───────────────────┐
│ JAMA Demo Data    │  │ IcePanel Demo Data│
│ demo_data.py      │  │ demo_data.py      │
└───────────────────┘  └───────────────────┘
```

**Key Architecture Principles:**
- **Separation:** Agent orchestrates; MCP servers own data and search logic
- **Protocol:** Model Context Protocol via JSON-RPC 2.0 (HTTP + stdio)
- **Demo-safe:** JAMA/IcePanel use demo datasets; ADO uses real API via official MCP

---

## Data Flow Example

**Query:** "Show me work items for Jane Smith"

1. **Agent** analyzes query → decides to call `search_work_items` tool
2. **tools.py** receives call → forwards to `mcp_client.py`
3. **StdioMCPClient** builds JSON-RPC request → sends to Node.js subprocess
4. **Real ADO MCP Server** receives request → calls Azure DevOps REST API → returns actual work items
5. **StdioMCPClient** unwraps response → returns to agent
6. **Agent** formats answer → displays to user

---

## Component Details

### Agent Application (agent_app/)
| File | Purpose | Key Details |
|------|---------|-------------|
| `config.py` | Load settings from `.env` | Azure endpoint, agent ID, MCP URLs |
| `main.py` | Entry point & CLI loop | Health checks, user input, Rich UI |
| `tools.py` | 7 agent tool definitions | Each calls MCP client for data |
| `mcp_client.py` | JSON-RPC 2.0 HTTP + stdio clients | Builds requests, unwraps responses |

**Tools available to agent:**
- `search_requirements`, `get_requirement` → Demo MCP (JAMA)
- `search_components`, `get_component` → Demo MCP (IcePanel)
- `search_work_items`, `get_work_item` → Official ADO MCP (stdio)
- `list_related_artifacts` → Routes by ID prefix

### MCP Servers
| Server | Transport | Data Source | Details |
|--------|-----------|-------------|----------|
| Demo MCP (JAMA + IcePanel) | HTTP:7070 | `demo_data.py` | Unified Azure Function server |
| ADO MCP | stdio | **Real Azure DevOps API** | Official Microsoft MCP server |

**Each server:**
- Implements MCP protocol: `tools/list` and `tools/call` methods
- Returns JSON-RPC 2.0 wrapped responses
- Demo MCP runs as a local Azure Function

### Demo Data (demo_mcp_server/demo_data.py)
Python lists containing:
- **Requirements:** REQ-001 to REQ-003 (JAMA artifacts)
- **Work Items:** WI-101 to WI-112 (ADO tasks/stories/bugs)
- **Components:** COMP-201 to COMP-204 (Architecture elements)
- **Tests:** TEST-301 (Test case)

Each item includes `related_ids` for cross-system traceability.

---

## JSON-RPC 2.0 Protocol

**Request Format:**
```json
# HTTP example (Demo MCP):
# POST http://localhost:7070/api/mcp
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_requirements",
    "arguments": {"query": "authentication"}
  }
}
```

**Response Format:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"results\": [...], \"count\": 4}"
    }],
    "isError": false
  }
}
```

---

## Running the System

**Prerequisites:**
- Python 3.11+
- Azure Functions Core Tools
- Azure CLI (logged in)
- `.env` file with agent configuration

**Startup sequence:**
```bash
# Terminal 1: Start unified Demo MCP server (JAMA + IcePanel)
cd demo_mcp_server && func start --port 7070

# Terminal 4: Run agent
python -m agent_app.main
```

**Health check:** Dashboard shows server status (✓/✗) on startup

---

## Key Benefits

| Benefit | Description |
|---------|-------------|
| **MCP Standard** | Uses official Model Context Protocol (JSON-RPC 2.0) |
| **Testable** | Demo MCP can be tested via HTTP; ADO via stdio in agent |
| **Scalable** | Servers deploy independently; agent URL changes, not code |
| **Future-proof** | Replace demo data with real APIs without changing architecture |
| **Separation** | Agent orchestrates; servers own data and search logic |

---

## Migration Path

| Phase | Current State | Future State |
|-------|---------------|--------------|
| **Data** | Python lists in `demo_data.py` | Azure Blob/Cosmos DB or real SaaS APIs |
| **Deployment** | Local (localhost:7070) | Azure Functions (cloud URLs) |
| **Operations** | Read-only (search/get) | Add write operations if needed |

**To deploy:** Change MCP URLs in `.env` from `localhost` to Azure Function URLs. No code changes required.

---

## Technical Notes

- **Authentication:** Uses `DefaultAzureCredential` for Azure; demo MCP server has no auth (local only)
- **Threading:** Agent polls run status every 0.5s; MCP requests timeout at 30s
- **Error handling:** JSON-RPC errors and MCP tool errors handled separately
- **UI:** Rich library for terminal formatting (panels, tables, spinners, markdown)
