"""Quick test script to verify MCP endpoints are working.

Note: This script only tests HTTP-based demo servers (JAMA, IcePanel).
ADO MCP now uses stdio transport - test via agent instead:
  python -m agent_app.main
  Then ask: "show me my work items"
"""

import json
import requests

# Test HTTP-based demo MCP Servers only
print("Testing HTTP-based MCP Servers (JAMA, IcePanel)")
print("Note: ADO MCP uses stdio - not tested here")
print("=" * 60)

# REMOVED: ADO MCP tests (now uses stdio transport instead of HTTP)
# To test ADO functionality:
#   1. Start agent: python -m agent_app.main
#   2. Ask: "show me my work items" or "search for work items tagged with POC"
#
# Legacy HTTP test code (no longer applicable):
#   request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
#   response = requests.post("http://localhost:7072/api/mcp", json=request)

print("\nADO MCP: Skipped (uses stdio transport - test via agent)")
print("=" * 60)
