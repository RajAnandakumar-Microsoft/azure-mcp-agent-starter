
# Purpose
- Provide a single, universal instruction set for building agentic proof‑of‑concepts using the Microsoft Agent Framework and Azure AI Foundry.
- Preserve only validated rules, patterns, and constraints from the source documents and explicit PoC requirements.

# Default assumptions
- This repository contains agentic Proof‑of‑Concepts unless explicitly labeled “Production”.
- Code prioritizes correctness and clarity over performance tuning.
- Infrastructure and integrations may be simplified unless explicitly marked production‑ready.

# PoC-specific assumptions (Olympus Traceability MCP Demo)
- This PoC is a capabilities demo:
  - MCP wrappers MUST NOT call customer SaaS APIs (no JAMA/ADO/IcePanel production or tenant APIs).
  - MCP wrappers MUST use demo datasets (JSON/Blob/Cosmos) that mimic real artifacts and relationships.
- The agent MUST behave as a “navigation and glue layer”:
  - Retrieve, summarize, and link to artifacts.
  - Never create, modify, or replace authoritative artifacts.
- Every surfaced artifact MUST include a deep link:
  - Links MUST point to a demo viewer site or clearly labeled placeholder URLs.
- Tools MUST be read‑only:
  - Only search/get/list/relationships/impact-style traversal tools are allowed.
  - No create/update/delete tools are permitted.

# How Copilot should behave (always-on behavior rules)
- DO follow this document as the single source of truth for agentic POC work.
- DO search the codebase for existing patterns before writing new code.
- DO read solution_*.py files when they exist and mirror their patterns.
- DO preserve TODO comment structures in lab_*.py files.
- DO keep changes minimal and aligned to existing style.
- DON’T assume APIs, SDKs, or conventions without verification.
- DO bias toward the simplest implementation that demonstrates the capability.
- DO avoid introducing production-hardening unless explicitly requested.

# Technology standards (languages, frameworks, clients, APIs)
- Language: Python 3.10+ is standard.
- Framework: Microsoft Agent Framework is required for agents.
- Semantic Kernel is an additional tool in the toolbelt for agentic POCs when clients need cross‑provider middleware, plugins, or prompt templating.

## Clients / API surfaces
- Preferred client for agents by default: `AzureOpenAIResponsesClient` with the Responses API.
- Allowed agent host path: `ChatAgent` + `AzureAIAgentClient` only when targeting the Foundry Agent Service.
- DON’T use `AzureOpenAIChatClient` (legacy Chat Completions).

## Tooling conventions
- Tool decorator: use `@ai_function` for agent tools; docstring becomes the tool description.
- Tool descriptions MUST be explicit and accurate (avoid vague descriptions).

## Authentication (PoC rules)
- Prefer Azure AD (DefaultAzureCredential/AzureCliCredential) when supported end-to-end.
- For demo MCP wrappers hosted in Azure Functions, key-based auth is permitted:
  - function keys and/or API-key headers are allowed for demo endpoints.
- Never hardcode secrets. Store secrets in env vars locally and Key Vault in Azure when deployed.
- Never pass secrets via prompts. Do not embed secrets in agent messages or tool outputs.

## Foundry SDK usage
- Foundry SDK usage (current GA / classic Foundry projects): use `AIProjectClient` for project setup, then an OpenAI‑compatible client for models/agents via the project endpoint.
- SDK versioning: 1.x targets Foundry classic; 2.x preview targets new Foundry. Match sample code to installed SDK.

## Stack options by layer (PoC default)
- Backend API (optional): FastAPI (async).
- Frontend (optional): React + TypeScript (only when UI is required).
- Data (PoC default): JSON fixtures first; optionally Blob Storage or Cosmos DB if needed.
- Observability (optional): OpenTelemetry; App Insights where available.
- CLI tooling: Typer for CLI interfaces and Rich for terminal UX.

# Architecture patterns for agentic POCs

## Default architecture (when building full POCs)
- UI → FastAPI API → Agent orchestration → Data layer (JSON/Blob/Cosmos/AI Search)

## Agent usage guardrails
- Use agents only when multi‑turn state, tool calling, or agent behavior is explicitly required.
- DON’T introduce agents for single‑shot generation or simple transformations.

## MCP wrapper pattern (Azure Functions) — REQUIRED for this PoC
- Each external “system” is represented by an MCP server hosted as an Azure Function endpoint.
- MCP servers MUST expose read-only tools only: search/get/list/relationships/deeplink/impact-traversal.
- MCP responses MUST use a standard response envelope:
  - `source_system`, `artifact_type`, `stable_id`, `title`, `summary`, `deeplink_url`, `related[]`
- Foundry Agent MUST connect to multiple MCP servers as tools:
  - each MCP server MUST have a unique `server_label` and `server_url`.
- Tool allowlisting:
  - If supported by the agent runtime, explicitly allowlist tool names and block everything else.
- Logging:
  - Log tool invocations (tool name, latency, returned IDs/counts, server_label).
  - Do not log raw artifact bodies if they could be sensitive.

## Deep-linking rules — REQUIRED
- Every artifact returned to the user MUST include a clickable deep link.
- Deep links MUST be stable and deterministic:
  - Use a demo viewer host + predictable routes, or a placeholder URL pattern.
- Deep links are the primary value primitive: return links first, summaries second.

## Cross-system traceability (demo graph) — REQUIRED
- Demo data MUST include relationships that allow:
  - requirement ↔ mitigation ↔ story ↔ test ↔ architecture component
- Implement “what’s related?” and “what might be impacted?” via graph traversal:
  - 1-hop and 2-hop neighbors are sufficient for PoC.

## Clarifying questions (ambiguity handling) — REQUIRED
- If the request is ambiguous, the agent MUST ask a clarifying follow-up:
  - Examples: Which project? Which system (requirements vs work items vs architecture)? Which component?
- Prefer one concise question at a time.
- When possible, suggest common follow-ups:
  - Example: “Do you also want related ADO stories and IcePanel components?”

## RAG rules (apply ONLY to retrieval-based POCs)
- RAG must be explicitly required by the POC.
- DON’T introduce embeddings, vector search, chunking, or citations unless retrieval is required.
- If RAG is used:
  - Use hybrid search (keyword + vector) in Azure AI Search.
  - Ground responses and include citations using filenames/IDs (simple inline/bracketed).

## Agent vs direct LLM
- Use agents for multi‑turn conversations and tool orchestration.
- Use direct LLM calls for single‑turn tasks (summarization, generation, classification).

# Deployment constraints (Azure policy)
- This PoC intends to host MCP wrappers on Azure Functions.
- If an environment policy prevents Azure Functions (e.g., shared keys restrictions), fallback to Container Apps.
- Prefer managed identity for Azure resources where supported.
- Keep deployment minimal and demo-friendly.

# Coding standards (typing, formatting, async rules)
- All functions and methods MUST include type hints.
- Use Pydantic models for validation and API response schemas.
- Formatting and linting:
  - Use Ruff for lint and format.
  - Line length: 88.
  - Import order: standard library → third‑party → local.
- Naming conventions:
  - snake_case for functions/variables.
  - PascalCase for classes.
  - UPPER_SNAKE_CASE for constants.
- Async rules:
  - FastAPI routes MUST be async; all I/O MUST be awaited.
  - CLI tools SHOULD be synchronous unless concurrently calling external APIs.
- Classes vs functions:
  - Prefer functions.
  - Use classes only for stateful clients, Pydantic/dataclasses, or complex state.
- Agent threading:
  - Always pass `thread` to `agent.run()` as a keyword argument.
- Entry points:
  - Use `asyncio.run()` for async entry points.
- Documentation:
  - Public functions/classes MUST have docstrings.
  - Complex logic MUST include short “why” comments.

# Security & secrets
- Never hardcode secrets.
- Store secrets in environment variables.
- Use dotenv locally; keep `.env` out of version control and provide `.env.example`.
- Validate and sanitize all user inputs before sending to LLMs.
- Validate file paths to prevent path traversal.
- Validate URL inputs to prevent SSRF where applicable.
- Prevent command injection; never use `shell=True`.

# Error handling & logging
- Wrap all external I/O in try/except blocks.
- Surface meaningful error messages.
- Use the logging module; never use print for errors.
- Include operation context in logs (what failed, inputs).

# Testing expectations
- Use pytest.
- Use pytest‑cov with `.coveragerc`.
- Coverage expectations:
  - Demo / Prototype: minimum 40%.
  - Production: minimum 80%.
- Production PRs require 85%+ coverage.
- Coverage must not regress.
- Tests must pass before merging.
- Entry points and scripts may be excluded via `.coveragerc`.

# Before writing/editing code checklist
- Run semantic search to identify existing patterns.
- Review `solution_*.py` reference implementations when present.
- Review existing `app/` or module patterns before adding new code.
- Confirm correct client class and API surface for the chosen approach.
- Preserve instructional TODOs and lab structure.
- Ensure `az login` has been run before executing Azure‑authenticated scripts.
- Confirm Foundry region supports MCP tool usage before provisioning resources.
- Confirm PoC mode: demo datasets only; no customer SaaS API calls.

# Decisions & Rationale (conflicts resolved)
- Responses API vs Chat Completions:
  - Decision: Standardize on Responses API.
  - Rationale: Modern, recommended training path.
- `AzureOpenAIResponsesClient` vs `ChatAgent` + `AzureAIAgentClient`:
  - Decision: Default to `AzureOpenAIResponsesClient`; use `ChatAgent` path only for Foundry Agent Service.
  - Rationale: Single primary client with optional hosted agent support.
- Azure AI Foundry vs Azure OpenAI Service:
  - Decision: Azure AI Foundry by default.
  - Rationale: Multi‑provider models and project alignment.
- Azure Functions vs Container Apps:
  - Decision: Azure Functions for MCP wrappers in this PoC; fallback to Container Apps if policy blocks Functions.
  - Rationale: Functions are simplest for demo MCP endpoints.
- Live SaaS APIs vs demo datasets:
  - Decision: Demo datasets only for this PoC.
  - Rationale: Capabilities demo; avoids customer tenant dependencies.
