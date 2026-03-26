# agent_app

Azure AI Foundry agent that queries multiple MCP servers simultaneously — config-driven server registration, per-server auth, read-only safety enforcement, and normalized responses with deep links.

## Prerequisites

1. **Python 3.10+**
2. **Azure AI Foundry Project with Existing Agent**
   - Create a project in [Azure AI Foundry](https://ai.azure.com)
   - Create an agent in the Foundry Agent Service
   - Note the agent ID, project endpoint, and subscription ID
3. **Azure CLI (Required)**
   - Run `az login` for Azure AD authentication

## Setup

### 1. Create Virtual Environment

```powershell
# From the repository root
cd agent_app
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the **repository root** (not inside `agent_app/`):

```bash
# Copy the example file
cp ..\.env.example ..\.env
```

Edit `..\.env` and set your Azure AI Foundry credentials:

```env
# Azure AI Foundry Configuration
AZURE_EXISTING_AGENT_ID="your-agent-id:1"
AZURE_ENV_NAME="your-env-name"
AZURE_LOCATION="eastus2"
AZURE_SUBSCRIPTION_ID="your-subscription-id"
AZURE_EXISTING_AIPROJECT_ENDPOINT="https://your-project.services.ai.azure.com/api/projects/your-project"
AZURE_EXISTING_AIPROJECT_RESOURCE_ID="/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.CognitiveServices/accounts/{account}/projects/{project}"
AZURE_EXISTING_RESOURCE_ID="/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.CognitiveServices/accounts/{account}"
AZD_ALLOW_NON_EMPTY_FOLDER=true

# Agent Configuration (optional)
AGENT_MAX_TOKENS=1000
AGENT_TEMPERATURE=0.7
```

### 4. Log in to Azure

```powershell
az login
```

## Running the Agent

### From the agent_app directory:

```powershell
python -m agent_app.main
```

### From the repository root:

```powershell
python -m agent_app.main
```

### Example Interaction

```
Agent ready. Enter your question (or 'exit' to quit):

> What's related to REQ-001?

================================================================================
AGENT RESPONSE:
================================================================================

REQ-001 links to work item WI-101 and architecture component COMP-201.
Deep link: https://demo-viewer.example.com/jama/REQ-001

================================================================================
```

## Running Tests

```powershell
# Run all tests
pytest

# Run with coverage
pytest --cov=agent_app --cov-report=term-missing

# Run with verbose output
pytest -v
```

## Project structure

```
agent_app/
├── auth/                # Per-server auth providers (api_key, PAT, OAuth, anonymous)
├── normalization/       # Response normalizer — standard envelope across all servers
├── registry/            # ServerRegistry — loads mcp_servers.yaml
├── tests/               # Unit tests
├── config.py            # Environment loading and typed configuration
├── main.py              # Entry point and agent run loop
├── mcp_client.py        # JSON-RPC 2.0 HTTP + stdio MCP clients
├── mcp_utils.py         # Parallel MCP fetch utilities
├── requirements.txt     # Python dependencies
└── tools.py             # Agent tool definitions
```

## Error reference

| Error | Cause | Fix |
|---|---|---|
| `AZURE_EXISTING_AIPROJECT_ENDPOINT not set` | Missing `.env` | Create `.env` from `.env.example` |
| `Unauthorized` | Not logged in | Run `az login` |
| `Cannot find agent` | Wrong agent ID | Verify ID in Azure AI Foundry portal |
| `DeploymentNotFound` | Wrong deployment name | Check deployed models in your Foundry project |

## Development notes

- **Authentication:** Azure AD (`DefaultAzureCredential`) via `az login`.
- **Formatting:** Ruff, 88-char line length, double quotes.
- **Type safety:** All functions include type hints.
