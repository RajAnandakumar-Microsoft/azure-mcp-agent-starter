# Auth Configuration Patterns

Recipes for common authentication scenarios.

---

## 1. No auth (local dev)

```yaml
auth:
  type: none
```

Use for local development servers or MCP servers running on a trusted network
with no authentication requirement.

---

## 2. Azure Function key (most common for HTTP servers)

```yaml
auth:
  type: api_key
  header: "x-functions-key"
  env_var: MY_SERVER_FUNCTION_KEY
```

`.env`:
```
MY_SERVER_FUNCTION_KEY=your-azure-function-key
```

Retrieve the key from:
> Azure Portal → Your Function App → App keys → Function keys

---

## 3. Azure DevOps PAT (official ADO MCP server)

```yaml
auth:
  type: pat
  env_var: ADO_MCP_AUTH_TOKEN
  stdio_auth_flag: "--authentication"
  stdio_auth_value: "envvar"
```

`.env`:
```
ADO_MCP_AUTH_TOKEN=your-ado-pat-here
```

Create a PAT at: https://dev.azure.com/YOUR_ORG/_usersSettings/tokens

Required PAT scopes (read-only):
- Work Items: **Read**
- Code: **Read** (if code search is needed)
- Project and Team: **Read**

---

## 4. GitHub PAT (for GitHub MCP server)

```yaml
auth:
  type: pat
  env_var: GITHUB_PAT
```

`.env`:
```
GITHUB_PAT=ghp_your_token_here
```

The PAT is sent as `Authorization: Bearer <token>`. GitHub also accepts it
as a query parameter for some endpoints, but the header approach is standard.

---

## 5. Multi-tenant ADO (different orgs)

Use separate server labels, each with its own env var:

```yaml
- label: ado_org_a
  transport: stdio
  command: node
  args: ["${ADO_MCP_PATH}", "${ORG_A_NAME}"]
  auth:
    type: pat
    env_var: ORG_A_ADO_PAT
    stdio_auth_flag: "--authentication"
    stdio_auth_value: "envvar"
  read_only: true

- label: ado_org_b
  transport: stdio
  command: node
  args: ["${ADO_MCP_PATH}", "${ORG_B_NAME}"]
  auth:
    type: pat
    env_var: ORG_B_ADO_PAT
    stdio_auth_flag: "--authentication"
    stdio_auth_value: "envvar"
  read_only: true
```

`.env`:
```
ORG_A_NAME=my-org-a
ORG_A_ADO_PAT=pat-for-org-a

ORG_B_NAME=my-org-b
ORG_B_ADO_PAT=pat-for-org-b
```

---

## 6. OAuth / Delegated auth (advanced)

The `oauth` auth type is currently a stub. See `agent_app/auth/oauth.py` for
implementation guidance using MSAL or `azure-identity`.

For Azure resources (ADO, Azure AI Foundry, etc.) that support Azure AD:
- Run `az login --tenant <tenant-id>` before starting the agent.
- Use `DefaultAzureCredential` which picks up the CLI token automatically.
- The existing agent already uses `DefaultAzureCredential` for Azure AI Foundry.

```yaml
auth:
  type: oauth
  tenant_id: "your-tenant-id"
  client_id: "your-app-registration-id"
```

---

## Secret management

| Environment | How to store secrets |
|-------------|----------------------|
| Local dev | `.env` file (listed in `.gitignore`) |
| Azure (deployed) | Azure Key Vault + Managed Identity |
| CI/CD | GitHub Secrets / Azure DevOps Variable Groups |

Never hardcode secrets in `mcp_servers.yaml` or source files.
Use `${ENV_VAR}` references in the YAML and set the env var externally.
