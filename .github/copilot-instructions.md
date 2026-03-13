# azure-mcp-agent-starter  Copilot Instructions

## Purpose
- Provide a single instruction set for building agentic proof-of-concepts using the Microsoft Agent Framework and Azure AI Foundry.
- This is a **public starter kit**  instructions are intentionally generic and reusable across projects and engagements.
- Serve as a reference implementation for connecting an Azure AI Foundry agent to multiple MCP servers with per-server auth.

## What this repo demonstrates
- An Azure AI Foundry agent connected to multiple MCP servers simultaneously.
- Config-driven server registration via `mcp_servers.yaml`  add/remove servers without code changes.
- Per-server authentication (API key, PAT, OAuth stub, anonymous).
- Read-only safety enforcement at the registry layer  write tools are blocked before they reach any server.
- Standard response normalization across heterogeneous MCP server responses.
- Demo MCP server hosted as Azure Functions with JSON fixture data.

## Key constraint: this is a demo, not a production system
- MCP servers in this repo use **demo datasets only**  no real SaaS tenant or customer APIs are called.
- When adapting for a real engagement, swap demo data for your own data sources.
- The agent is a "navigation and glue layer": retrieve, summarize, and link. Never create, modify, or delete authoritative artifacts.
- Every artifact returned to the user MUST include a deep link (demo viewer URL or placeholder).
- Tools MUST be read-only: search/get/list/relationships/impact traversal only.

## How Copilot should behave
- DO follow this file as the single source of truth for all agent-related work in this repo.
- DO search the codebase for existing patterns before writing new code.
- DO keep changes minimal and aligned to existing style.
- DO bias toward the simplest implementation that demonstrates the capability.
- DON'T assume APIs, SDKs, or conventions without verification  read the existing code first.
- DON'T add production-hardening (retry logic, circuit breakers, caches) unless explicitly requested.
- DON'T add new dependencies without checking `agent_app/requirements.txt` first.

## Repository layout
```
azure-mcp-agent-starter/
 .github/
    copilot-instructions.md   # This file  Copilot behavior rules
 agent_app/                     # Main agent application
    auth/                      # Per-server auth providers
    registry/                  # Config-driven server registry
    normalization/             # Response envelope normalizer
    config.py                  # Environment loading & typed config
    main.py                    # Agent run loop (entry point)
    tools.py                   # Agent tool definitions
    mcp_client.py              # JSON-RPC 2.0 HTTP + stdio MCP clients
    mcp_utils.py               # Parallel MCP fetch utilities
    tests/                     # All unit tests
 demo_mcp_server/               # Azure Function demo MCP server
    function_app.py            # MCP endpoint (JAMA + IcePanel demo)
    demo_data.py               # Demo fixtures
    mcp_response.py            # Standard response envelope helper
 examples/                      # Guides for extending the kit
 mcp_servers.yaml               # Server registry config (edit this to add servers)
 QUICKSTART.md                  # 5-minute setup guide
 .env.example                   # Environment variable template
```

## Technology standards

### Language & framework
- Python 3.10+ required.
- Microsoft Agent Framework (`azure-ai-agents`) for the agent runtime.
- Semantic Kernel is available as an additional tool when cross-provider middleware or prompt templating is needed.

### Client / API surface
- Preferred agent client: `AzureOpenAIResponsesClient` with the Responses API.
- Use `ChatAgent` + `AzureAIAgentClient` only when targeting the Foundry Agent Service directly.
- DON'T use `AzureOpenAIChatClient` (legacy Chat Completions path).

### Tooling conventions
- Use `@ai_function` as the decorator for agent tools; the docstring becomes the tool description.
- Tool descriptions MUST be explicit and accurate  avoid vague descriptions like "does stuff".

### Authentication
- Prefer Azure AD (`DefaultAzureCredential` / `AzureCliCredential`) end-to-end.
- For demo MCP servers on Azure Functions, API key auth (function keys / `x-functions-key` header) is acceptable.
- Never hardcode secrets. Use env vars locally; use Key Vault when deployed.
- Never pass secrets through prompts or embed them in tool outputs.

### MCP server registry (`mcp_servers.yaml`)
- Every MCP server has a unique `label` used as its identifier throughout the codebase.
- Auth is declared per-server under the `auth:` block  no auth config lives in Python code.
- All servers default to `read_only: true`. The registry blocks write-prefixed tool names before any call goes out.
- Use `${ENV_VAR}` or `${ENV_VAR:-default}` in URL/args fields for environment-specific values.

### Adding a new MCP server
1. Add an entry in `mcp_servers.yaml` with `label`, `transport`, `url`/`command`, and `auth`.
2. If the server returns non-standard response shapes, register a custom adapter via `register_adapter()` in `agent_app/normalization/normalizer.py`.
3. Add a tool function in `agent_app/tools.py` that calls `get_mcp_client("your-label")`.
4. Write tests in `agent_app/tests/`.
5. No changes to `config.py`, `mcp_client.py`, or `registry/` are required.

### Stack options by layer
- Backend API (optional): FastAPI (async).
- Frontend (optional): React + TypeScript (only when a UI is explicitly required).
- Data (default): JSON fixtures first; optionally Blob Storage or Cosmos DB.
- Observability (optional): OpenTelemetry; Application Insights when available.
- CLI / terminal UX: Typer for CLI, Rich for terminal output.

## Architecture patterns

### Default data flow
```
User  main.py  AgentsClient (Foundry)  tools.py  ServerRegistry  AuthProvider  MCP server  Normalizer  response
```

### Agent usage guardrails
- Use agents only when multi-turn state, tool calling, or orchestration is explicitly required.
- DON'T introduce agents for single-shot generation or simple text transformations.

### MCP wrapper pattern (Azure Functions)
- Each external system is represented by one MCP server (one Azure Function app).
- MCP servers expose read-only tools only: search / get / list / relationships / impact traversal.
- MCP responses use a standard envelope: `source_system`, `artifact_type`, `stable_id`, `title`, `summary`, `deeplink_url`, `related[]`.
- Log every tool invocation: tool name, latency, returned IDs/counts, server label.
- Do not log raw artifact bodies if they might contain sensitive data.

### Deep-linking rules
- Every artifact returned to the user MUST include a clickable deep link.
- Deep links MUST be stable and deterministic  use predictable URL routes, not session-based URLs.
- Return links first, summaries second.

### Cross-system traceability
- Demo data MUST express relationships that allow graph traversal:
  - requirement  work item  test  architecture component
- 1-hop and 2-hop traversal is sufficient for a PoC.

### Clarifying questions
- If a user request is ambiguous, the agent MUST ask one concise clarifying question before proceeding.
- Suggest the most likely follow-up: "Do you also want related work items and architecture components?"

### RAG (retrieval-augmented generation)
- RAG must be explicitly required  don't add embeddings, vector search, or chunking by default.
- If RAG is needed, use hybrid search (keyword + vector) in Azure AI Search with inline/bracketed citations.

## Coding standards

### Types, formatting, naming
- All functions and methods MUST have type hints.
- Use Pydantic models for validation and API response schemas.
- Ruff for linting and formatting; line length 88; double quotes.
- Import order: standard library  third-party  local.
- `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.

### Async rules
- FastAPI routes MUST be async; all I/O MUST be awaited.
- CLI tools should be synchronous unless making concurrent external calls.

### Classes vs functions
- Prefer functions. Use classes for stateful clients, Pydantic models, or complex state.

### Documentation
- Public functions and classes MUST have docstrings.
- Complex logic MUST have a short "why" comment, not a "what" comment.

## Security
- Never hardcode secrets  env vars only.
- Keep `.env` out of version control; always provide a `.env.example`.
- Validate and sanitize all user inputs before passing them to LLMs.
- Validate file paths to prevent path traversal.
- Validate URL inputs to prevent SSRF.
- Never use `shell=True` in subprocess calls.

## Error handling & logging
- Wrap all external I/O in `try/except` blocks with meaningful error messages.
- Use the `logging` module; never use `print()` for errors.
- Include context in log messages: what operation failed and what the inputs were.

## Testing
- Use `pytest` + `pytest-asyncio`.
- Coverage via `pytest-cov`.
- Minimum coverage: 40% for PoC/demo work, 80% for production.
- Tests must pass before merging. Coverage must not regress.
- Run tests: `pytest agent_app/tests/ -v`

## Deployment defaults
- MCP servers  Azure Functions (fallback: Container Apps if function key policy blocks deployment).
- Prefer managed identity for all Azure resource access.
- Keep deployments minimal and demo-friendly  no unnecessary infrastructure.

## Architecture decisions

| Decision | Choice | Reason |
|---|---|---|
| Agent client | `AzureOpenAIResponsesClient` (default); `ChatAgent` for Foundry Agent Service | Single modern client with optional hosted agent support |
| AI platform | Azure AI Foundry | Multi-provider models and project-scoped management |
| MCP host | Azure Functions | Simplest demo endpoint; Container Apps as fallback |
| Data layer | JSON fixtures  Blob/Cosmos | Start simple; migrate when data volume requires it |
| Live APIs | Demo datasets only | Capabilities demo; avoids real tenant dependencies |
