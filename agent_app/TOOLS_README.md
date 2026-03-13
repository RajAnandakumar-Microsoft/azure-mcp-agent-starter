# Agent Tools Documentation

## Overview

The MCP Traceability Agent now includes **7 local tools** that provide read-only access to demo datasets across three systems: JAMA (requirements), Azure DevOps (work items), and IcePanel (architecture components).

## Available Tools

### JAMA Requirements Tools

#### `search_requirements(query: str)`
Search for requirements by keyword or ID.

**Example usage:**
- "Search for authentication requirements"
- "Find requirements about encryption"

**Returns:** List of matching requirements with IDs, titles, status, priority, and deep links.

#### `get_requirement(requirement_id: str)`
Retrieve detailed information for a specific requirement.

**Example usage:**
- "Get details for requirement REQ-001"
- "Show me REQ-002"

**Returns:** Full requirement details including description, status, priority, relationships, and deep link.

### Azure DevOps Tools

#### `search_work_items(query: str)`
Search for work items (user stories, tasks, bugs) by keyword or ID.

**Example usage:**
- "Find work items related to OAuth"
- "Search for authentication work items"

**Returns:** List of matching work items with IDs, types, titles, states, and deep links.

#### `get_work_item(work_item_id: str)`
Retrieve detailed information for a specific work item.

**Example usage:**
- "Get details for work item WI-101"
- "Show me WI-102"

**Returns:** Full work item details including type, description, state, assignment, relationships, and deep link.

### IcePanel Architecture Tools

#### `search_components(query: str)`
Search for architecture components by keyword or ID.

**Example usage:**
- "Find components related to authentication"
- "Search for microservices"

**Returns:** List of matching components with IDs, names, types, technologies, and deep links.

#### `get_component(component_id: str)`
Retrieve detailed information for a specific architecture component.

**Example usage:**
- "Get details for component COMP-201"
- "Show me COMP-202"

**Returns:** Full component details including name, type, description, technology, relationships, and deep link.

### Cross-System Tools

#### `list_related_artifacts(artifact_id: str)`
List all artifacts related to a given requirement, work item, component, or test.

**Example usage:**
- "What artifacts are related to requirement REQ-001?"
- "Show me everything connected to WI-101"
- "What's related to COMP-201?"

**Returns:** Related artifacts grouped by type (requirements, work items, components, tests) with IDs, titles, and deep links.

## Tool Implementation Details

### Technology Stack
- **Tool Definitions:** `FunctionToolDefinition` + `FunctionDefinition` from `azure.ai.agents.models`
- **Tool Execution:** Local Python functions with JSON return values
- **Data Layer:** In-memory demo datasets in `agent_app/demo_data.py`

### Tool Calling Flow
1. User asks a question
2. Agent analyzes the question and selects appropriate tools
3. Agent calls tools with extracted parameters
4. Local Python functions execute and return JSON results
5. Agent processes tool outputs and synthesizes a response
6. Agent presents results with formatted text and deep links

### Deep Links
Every artifact returned includes a `deeplink_url` field:
- **Format:** `https://demo-viewer.example.com/{system}/{artifact_id}`
- **Systems:** `jama`, `ado`, `icepanel`, `tests`
- **Purpose:** Provides direct navigation to artifact details (demo URLs for POC)

### Demo Data Summary
- **Requirements:** 3 JAMA requirements (REQ-001, REQ-002, REQ-003)
- **Work Items:** 3 ADO work items (WI-101, WI-102, WI-103)
- **Components:** 4 IcePanel components (COMP-201 through COMP-204)
- **Tests:** 1 test case (TEST-301)
- **Relationships:** Cross-referenced IDs link artifacts across systems

## Testing

### Manual Testing
Run the agent interactively:
```powershell
.\agent_app\venv\Scripts\python.exe -m agent_app.main
```

Try these sample queries:
- "Search for authentication requirements"
- "Get details for requirement REQ-002"
- "What artifacts are related to requirement REQ-001?"
- "Find work items related to OAuth"
- "Show me architecture components for authentication"

### Automated Testing

#### Test tool functions directly:
```powershell
$env:PYTHONPATH='<path-to-workspace>'
.venv\Scripts\python.exe test_tools.py
```

#### Test agent with tool calling:
```powershell
$env:PYTHONPATH='<path-to-workspace>'
.venv\Scripts\python.exe test_agent_tools.py
```

## Next Steps (Phase 2)

Now that local tools are working, the next phase will:

1. **Build MCP Server Wrappers** - Deploy Azure Functions that expose these tools as MCP servers
2. **Implement Real-Time Demo Viewer** - Create a simple web viewer for deep links
3. **Add Impact Analysis** - Extend `list_related_artifacts` to support 2-hop traversal
4. **Add Clarifying Questions** - Teach agent to ask for disambiguation when needed
5. **Add RAG Capabilities** - Enable semantic search over artifact content (if required)

## Architecture Notes

### Why Local Tools First?
- **Validate Tool Calling Pattern:** Ensures agent can invoke tools correctly before adding MCP complexity
- **Fast Iteration:** Local Python functions are easier to debug than remote MCP endpoints
- **POC Scope:** Demo datasets sufficient for capabilities demonstration
- **Read-Only Constraint:** All tools follow repo standard (no create/update/delete operations)

### Transition to MCP Servers
When ready to build MCP servers:
- Tool definitions will move to Azure Functions
- Tool functions will become HTTP endpoints
- Agent will call MCP servers instead of local functions
- Same tool signatures and return formats will be preserved
- `TOOL_FUNCTIONS` mapping becomes HTTP client
