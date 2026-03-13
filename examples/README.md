# Examples

This folder contains worked examples for extending the starter kit with new MCP servers.

---

## What's in this folder

| Path | Purpose |
|------|---------|
| `custom_http_server/` | Template for a new HTTP MCP server (Azure Functions) |
| `custom_stdio_server/` | Template for a custom stdio MCP server (Python subprocess) |
| `auth_patterns.md` | Auth configuration recipes for common scenarios |

The existing `demo_mcp_server/` at the repo root is a fully working HTTP MCP server
example (JAMA + IcePanel demo data). Use it as a reference implementation.

---

## Quick reference: adding a new MCP server

### Step 1 — Register the server in `mcp_servers.yaml`

```yaml
servers:
  # ... existing entries ...

  - label: my_system          # unique label used in code
    description: "My system"
    transport: http            # or stdio
    url: "https://my-server.azurewebsites.net/api"
    auth:
      type: api_key
      header: "x-functions-key"
      env_var: MY_SYSTEM_KEY   # set this in .env
    read_only: true            # always true unless you have a specific reason
```

No code changes are required — the registry picks up the new entry automatically.

### Step 2 — Add the env var to `.env`

```env
MY_SYSTEM_KEY=your-function-key-here
```

### Step 3 — (Optional) Register a response adapter

If your server returns a non-standard schema, register a custom adapter so the
agent sees a consistent envelope:

```python
# In your app startup or a dedicated adapters.py module:
from agent_app.normalization import register_adapter

def my_system_adapter(raw: dict) -> dict:
    return {
        "source_system": "My System",
        "artifact_type": raw.get("kind", "item"),
        "stable_id": raw["id"],
        "title": raw["name"],
        "summary": raw.get("description", ""),
        "deeplink_url": f"https://my-system.example.com/items/{raw['id']}",
        "related": raw.get("links", []),
    }

register_adapter("my_system", my_system_adapter)
```

Servers that already emit the standard envelope (all envelope fields present) are
normalized automatically — no adapter needed.

---

## Transport cheat sheet

| Use case | Transport | Config |
|----------|-----------|--------|
| Azure Function / REST API | `http` | `url: https://...` |
| Official Microsoft MCP (ADO, GitHub) | `stdio` | `command: node`, `args: [path, org]` |
| Local Python MCP server | `stdio` | `command: python`, `args: [script.py]` |
| Docker-hosted MCP | `http` | `url: http://localhost:PORT/api` |

---

## Auth cheat sheet

| Scenario | Auth type | Key config fields |
|----------|-----------|-------------------|
| Azure Functions (anonymous/local) | `none` | — |
| Azure Functions (key-protected) | `api_key` | `header`, `env_var` |
| Azure DevOps PAT | `pat` | `env_var`, `stdio_auth_flag`, `stdio_auth_value` |
| GitHub PAT | `pat` | `env_var` |
| Azure AD / multi-tenant | `oauth` | see `agent_app/auth/oauth.py` |

---

## Multi-tenant scenarios

When your users connect to different tenants/orgs:
- Use a separate server entry per tenant in `mcp_servers.yaml`.
- Each entry gets its own auth block and env var.
- Env vars can be prefixed by tenant: `TENANT_A_ADO_PAT`, `TENANT_B_ADO_PAT`.

```yaml
- label: ado_tenant_a
  transport: stdio
  command: node
  args: ["${ADO_MCP_PATH}", "${TENANT_A_ADO_ORG}"]
  auth:
    type: pat
    env_var: TENANT_A_ADO_PAT
    stdio_auth_flag: "--authentication"
    stdio_auth_value: "envvar"
  read_only: true

- label: ado_tenant_b
  transport: stdio
  command: node
  args: ["${ADO_MCP_PATH}", "${TENANT_B_ADO_ORG}"]
  auth:
    type: pat
    env_var: TENANT_B_ADO_PAT
    stdio_auth_flag: "--authentication"
    stdio_auth_value: "envvar"
  read_only: true
```

---

## Read-only enforcement

All servers default to `read_only: true`. The registry blocks any tool call whose
name starts with a write prefix (`create_`, `update_`, `delete_`, `patch_`, etc.)
before it reaches the MCP server.

This is a defence-in-depth measure — it does **not** replace proper server-side
access controls.

To inspect whether a specific tool is allowed:

```python
from agent_app.registry import get_registry

registry = get_registry()
allowed = registry.is_tool_allowed("my_system", "create_item")  # → False
```
