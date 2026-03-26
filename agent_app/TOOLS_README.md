# Agent Tools Documentation

## Overview

Read-only tools that call MCP servers across three demo systems: JAMA (requirements), Azure DevOps (work items), and IcePanel (architecture components).

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
- **Data Layer:** JSON fixture data in `demo_mcp_server/demo_data.py`

### Tool Calling Flow
1. User asks a question
2. Azure AI Foundry agent selects appropriate tools
3. Agent calls the tool with extracted parameters
4. Tool calls the MCP server via JSON-RPC 2.0 (`MCPClient`)
5. MCP server returns a response; `Normalizer` applies the standard envelope
6. Agent synthesizes a response with deep links

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

