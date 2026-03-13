# MCP Traceability Agent - Local Demo

This is the first vertical slice of the MCP Traceability Agent PoC. It demonstrates a local Python agent that uses Azure AI Foundry and the Microsoft Agent Framework to answer user questions.

## Current Status

**Phase 1: Basic Agent Loop (✅ Current)**
- Initializes Azure AI Foundry Responses API client
- Runs a simple agent conversation loop
- Accepts single-turn user input from CLI
- Streams agent responses
- No external SaaS API calls (demo mode only)

**Phase 2: MCP Server Integration (🚧 Next)**
- Connect to MCP servers for JAMA, ADO, IcePanel
- Read-only tool calls (search/get/list/relationships)
- Deep-linking support

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
```Before running: Login to Azure

```powershell
az login
```

### 

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
MCP Traceability Agent - Local Demo
================================================================================

NOTE: This is a demo. MCP server connections will be added next.

Enter your question (or 'exit' to quit):

> What can you help me with?

================================================================================
AGENT RESPONSE:
================================================================================

I'm the MCP Traceability Agent. Currently, I'm in a setup phase...
[response continues]

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

## Project Structure

```
agent_app/
├── __init__.py          # Package initialization
├── config.py            # Environment loading and typed configuration
├── main.py              # Entry point and agent run loop
├── requirements.txt     # Python dependencies
├── README.md            # This file
└── tests/
    ├── __init__.py
    └── test_config.py   # Configuration tests
```

## Error HandlingEXISTING_AIPROJECT_ENDPOINT
   ```
   Solution: Ensure `.env` file exists in the repository root with all required values.

2. **Authentication error:**
   ```
   Error during agent run: Unauthorized
   ```
   Solution: Run `az login` to authenticate with Azure AD.

3. **Agent not found:**
   ```
   Error: Cannot find agent 'your-agent-id:1' in your Foundry project.
   ```
   Solution: Verify the agent ID exists in your Foundry project. Check the agent list in Azure AI Foundry portal

3. **Deployment not found:**
   ```
   Error: DeploymentNotFound
   ```
   Solution: Ensure the deployment name matches a deployed model in your Foundry project.

## Next Steps

- [ ] Add MCP server integration (JAMA, ADO, IcePanel wrappers)
- [ ] Implement read-only tools for artifact retrieval
- [ ] Add deep-linkingUses Azure AD (DefaultAzureCredential) - requires `az login`.
- **Agent Service:** Uses existing agents from Foundry Agent Service (ChatAgent + AzureAIAgentClient)
- [ ] Add multi-turn conversation support

## Development Notes

- **Demo Mode Only:** This agent does NOT call customer SaaS APIs (JAMA/ADO/IcePanel).
- **Authentication:** Currently uses API key auth. Azure AD support can be added.
- **Single-Turn:** This version handles one question at a time. Multi-turn support coming next.
- **Formatting:** Code follows Ruff formatting (88 char line length).
- **Type Safety:** All functions include type hints per repo standards.
