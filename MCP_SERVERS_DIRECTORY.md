# Available MCP Servers

This guide lists official and community MCP servers you can plug into the agent
by adding entries to `mcp_servers.yaml`. No code changes are needed.

> **Canonical source:** [microsoft/mcp](https://github.com/microsoft/mcp) —
> the official Microsoft MCP catalog. Check there for the latest additions.

---

## How to add a server

Add an entry to `mcp_servers.yaml` at the repo root. The agent picks it up
automatically on next startup. See [QUICKSTART.md](QUICKSTART.md) and the
examples already in that file for the full field reference.

```yaml
servers:
  - label: my_server          # unique name used in code
    description: "What it does"
    transport: http            # or "stdio"
    url: "${MY_SERVER_URL}"    # for HTTP
    # command: node            # for stdio
    # args: ["path/to/index.js"]
    auth:
      type: api_key            # or pat, oauth, azure_identity, none
      header: "x-functions-key"
      env_var: MY_SERVER_KEY
    read_only: true
```

---

## Microsoft Official MCP Servers

### Most relevant to this agent

| Server | Transport | Auth | Description | Links |
|--------|-----------|------|-------------|-------|
| **Azure DevOps** | stdio | PAT / OAuth | Work items, PRs, builds, sprints, test plans. *Already configured in this repo.* | [Repo](https://github.com/microsoft/azure-devops-mcp) · [Docs](https://learn.microsoft.com/azure/devops/release-notes/2025/sprint-258-update) |
| **GitHub** | HTTP (remote) | OAuth | Repos, issues, PRs, code search, actions. | [Repo](https://github.com/github/github-mcp-server) |
| **Azure** | stdio | Azure Identity | 47+ Azure services — CosmosDB, KeyVault, Storage, App Service, AKS, etc. | [Repo](https://github.com/microsoft/mcp/tree/main/servers/Azure.Mcp.Server) · [Docs](https://learn.microsoft.com/azure/developer/azure-mcp-server/) |
| **Microsoft Foundry** | HTTP (remote) | OAuth | Models, knowledge, evaluation, agents. | [Docs](https://learn.microsoft.com/azure/ai-foundry/mcp/get-started) |

### Microsoft 365 & Productivity

All M365 servers below are **remote HTTP** endpoints at
`https://agent365.svc.cloud.microsoft/agents/tenants/{tenant_id}/servers/...`
and require **Entra ID (OAuth)** auth.

| Server | Endpoint suffix | Description | Source |
|--------|----------------|-------------|--------|
| **OneDrive & SharePoint** | `mcp_ODSPRemoteServer` | Files, docs, wikis. | [Repo](https://github.com/bap-microsoft/MCP-Platform/tree/main/src/Services/WebApi/MCPServers/FirstParty/FileBased/mcp_ODSPRemoteServer) |
| **SharePoint Lists** | `mcp_SharePointListsTools` | Lists, document libraries, sites. | [Repo](https://github.com/bap-microsoft/MCP-Platform/tree/main/src/Services/WebApi/MCPServers/FirstParty/FileBased/mcp_SharepointListsTools) |
| **Teams** | `mcp_TeamsServer` | Chats, channels, messages. | [Repo](https://github.com/bap-microsoft/MCP-Platform/tree/main/src/Services/WebApi/MCPServers/FirstParty/CodeBased/mcp_TeamsServer) |
| **Outlook Mail** | `mcp_MailTools` | Create, send, search emails. | [Repo](https://github.com/bap-microsoft/MCP-Platform/tree/main/src/Services/WebApi/MCPServers/FirstParty/CodeBased/mcp_MailTools) |
| **Calendar** | `mcp_CalendarTools` | Events, availability, invites. | [Repo](https://github.com/bap-microsoft/MCP-Platform/tree/main/src/Services/WebApi/MCPServers/FirstParty/CodeBased/mcp_CalendarTools) |
| **Copilot Chat** | `mcp_M365Copilot` | Search across M365 content. | [Repo](https://github.com/bap-microsoft/MCP-Platform/tree/main/src/Services/WebApi/MCPServers/FirstParty/CodeBased/mcp_M365Copilot) |
| **Word** | `mcp_WordServer` | Read, create, collaborate on docs. | [Repo](https://github.com/bap-microsoft/MCP-Platform/tree/main/src/Services/WebApi/MCPServers/FirstParty/CodeBased/mcp_WordServer) |
| **User / Org** | `mcp_MeServer` | User profile, manager, team, reports. | [Repo](https://github.com/bap-microsoft/MCP-Platform/tree/main/src/Services/WebApi/MCPServers/FirstParty/CodeBased/mcp_MeServer) |
| **Admin Center** | `mcp_AdminTools` | Tenant administration tools. | [Repo](https://github.com/bap-microsoft/MCP-Platform/tree/main/src/Services/WebApi/MCPServers/FirstParty/CodeBased/mcp_AdminTools) |

### Data & Analytics

| Server | Transport | Description | Links |
|--------|-----------|-------------|-------|
| **Microsoft Fabric** | stdio | Fabric workloads, APIs, item definitions. | [Repo](https://github.com/microsoft/mcp/tree/main/servers/Fabric.Mcp.Server) |
| **Fabric Real-Time Intelligence** | stdio | RTI querying and analysis. | [Repo](https://aka.ms/rti.mcp.repo) |
| **Microsoft SQL** | stdio | SQL Server / Azure SQL — queries, schema, CRUD. | [Repo](https://aka.ms/MssqlMcp) |
| **Dataverse** | stdio | Business data — tables, queries, records. | [Link](https://go.microsoft.com/fwlink/?linkid=2320176) |
| **Clarity** | stdio | Web analytics data export. | [Repo](https://github.com/microsoft/clarity-mcp-server) |

### Developer Tools

| Server | Transport | Description | Links |
|--------|-----------|-------------|-------|
| **Playwright** | stdio | Browser automation via accessibility snapshots. | [Repo](https://github.com/microsoft/playwright-mcp) |
| **Dev Box** | stdio | Manage Microsoft Dev Box environments. | [npm](https://www.npmjs.com/package/@microsoft/devbox-mcp) |
| **AKS** | stdio | Azure Kubernetes Service cluster operations. | [Repo](https://github.com/Azure/aks-mcp) |
| **NuGet** | stdio | NuGet package management and automation. | [Repo](https://github.com/NuGet/Home) |
| **Markitdown** | stdio | Markdown processing and document conversion. | [Repo](https://github.com/microsoft/markitdown) |
| **Microsoft Learn** | HTTP (remote) | Search official Microsoft documentation. | [Repo](https://github.com/microsoftdocs/mcp) |

### Security

| Server | Transport | Description | Links |
|--------|-----------|-------------|-------|
| **Microsoft Sentinel** | HTTP (remote) | Security data lake exploration. | [Docs](https://aka.ms/mcp/data-exploration) |

---

## Third-Party / Community MCP Servers

These are not maintained by Microsoft but are widely adopted in enterprise environments.
Verify compatibility and security before integrating.

### Directly relevant to this agent

These replace the demo MCP servers in this repo with connections to real instances.

| Server | Transport | Auth | Description | Links |
|--------|-----------|------|-------------|-------|
| **Jama Connect** (unofficial) | stdio | OAuth 2.0 (client credentials) | Read-only access to Jama requirements, items, relationships, projects. Wraps the official `py-jama-rest-client`. Supports mock mode for testing. | [Repo](https://github.com/t-j-thomas/jama-mcp-server) |
| **IcePanel** (official, beta) | stdio | API Key | Architecture diagrams, components, and relationships from IcePanel. Official server from IcePanel. | [Repo](https://github.com/IcePanel/mcp-server) · [npm](https://www.npmjs.com/package/@icepanel/mcp-server) |

#### Example: Jama Connect via stdio

```yaml
  - label: jama
    description: "Jama Connect — requirements management (live instance)"
    transport: stdio
    command: uv
    args:
      - "run"
      - "python"
      - "-m"
      - "jama_mcp_server.server"
    auth:
      type: none  # Auth handled via env vars below
    read_only: true
```

Set these env vars in your `.env`:
```
JAMA_URL=https://yourcompany.jamacloud.com
JAMA_CLIENT_ID=your-oauth-client-id
JAMA_CLIENT_SECRET=your-oauth-client-secret
```

> **Note:** The Jama MCP server must be cloned locally first — it is intentionally
> not published to PyPI. Run `uv sync` in the cloned directory before use.
> See: [github.com/t-j-thomas/jama-mcp-server](https://github.com/t-j-thomas/jama-mcp-server)

#### Example: IcePanel via stdio

```yaml
  - label: icepanel
    description: "IcePanel — architecture diagrams (live instance)"
    transport: stdio
    command: npx
    args:
      - "-y"
      - "@icepanel/mcp-server@latest"
      - "API_KEY=${ICEPANEL_API_KEY}"
      - "ORGANIZATION_ID=${ICEPANEL_ORG_ID}"
    auth:
      type: none  # Auth handled via CLI args
    read_only: true
```

Set these env vars in your `.env`:
```
ICEPANEL_API_KEY=your-api-key
ICEPANEL_ORG_ID=your-organization-id
```

> **Note:** Requires Node.js v18+. Get your org ID and API key from
> IcePanel → Organization Settings → API Keys.
> See: [github.com/IcePanel/mcp-server](https://github.com/IcePanel/mcp-server)

### Other enterprise servers

| Server | Source | Description | Relevance |
|--------|--------|-------------|-----------|
| **Atlassian (Jira + Confluence)** | [Atlassian Remote MCP](https://developer.atlassian.com/) | Issues, boards, sprints, Confluence pages. OAuth 2.0. | ⭐ Requirements traceability |
| **ServiceNow** | Community | ITSM tickets, incidents, change management. | Operational traceability |
| **Postgres / MySQL** | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | Direct database access for read queries. | Data integration |
| **Filesystem** | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | Local or cloud file tree access. | Document search |

### Suggested: servers to complete the traceability chain

The agent currently covers **requirements → work items → architecture**. These
servers would close remaining gaps:

| Gap | Server to look for | Why |
|-----|-------------------|-----|
| **Test management** | TestRail MCP, qTest MCP, or Xray for Jira MCP | Close the loop: requirement → work item → **test case** → architecture |
| **Source code** | GitHub MCP *(already listed above)* | Trace work items → **code changes** (PRs, commits) |
| **CI/CD pipelines** | Azure Pipelines *(in ADO MCP)*, GitHub Actions *(in GitHub MCP)* | Code → **builds** → deployments |
| **Documentation** | Confluence MCP, SharePoint MCP *(listed above)* | Requirements context and knowledge base |

> **Discovery registries:**
> - [GitHub MCP Registry](https://github.com/mcp/registry) — GitHub's curated directory
> - [MCP Center](https://mcp.azure.com/) — Microsoft's API catalog
> - [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) — Reference implementations

---

## Example: Adding an M365 Remote Server

```yaml
  - label: teams
    description: "Microsoft Teams — chats, channels, messages"
    transport: http
    url: "https://agent365.svc.cloud.microsoft/agents/tenants/${AZURE_TENANT_ID}/servers/mcp_TeamsServer"
    auth:
      type: oauth
      tenant_id: "${AZURE_TENANT_ID}"
      client_id: "${TEAMS_CLIENT_ID}"
      scopes:
        - "https://graph.microsoft.com/.default"
      client_secret_env_var: TEAMS_CLIENT_SECRET
    read_only: true
```

## Example: Adding GitHub MCP

```yaml
  - label: github
    description: "GitHub — repos, issues, PRs, code search"
    transport: http
    url: "https://api.githubcopilot.com/mcp/"
    auth:
      type: pat
      env_var: GITHUB_TOKEN
    read_only: true
```

## Example: Adding Jira (Atlassian)

```yaml
  - label: jira
    description: "Jira — issues, sprints, boards"
    transport: http
    url: "${JIRA_MCP_URL}"
    auth:
      type: oauth
      tenant_id: "${ATLASSIAN_TENANT_ID}"
      client_id: "${JIRA_CLIENT_ID}"
      scopes:
        - "read:jira-work"
      client_secret_env_var: JIRA_CLIENT_SECRET
    read_only: true
```
