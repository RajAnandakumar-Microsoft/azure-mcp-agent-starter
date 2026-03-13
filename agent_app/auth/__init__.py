"""Auth provider package for per-MCP-server authentication.

Supported types (configured via mcp_servers.yaml):
- none       → NoAuthProvider
- api_key    → ApiKeyAuthProvider
- pat        → PatAuthProvider
- oauth      → OAuthAuthProvider (stub; see oauth.py for implementation)
"""

from agent_app.auth.api_key import ApiKeyAuthProvider
from agent_app.auth.base import AuthProvider
from agent_app.auth.factory import build_auth_provider
from agent_app.auth.none_provider import NoAuthProvider
from agent_app.auth.oauth import OAuthAuthProvider
from agent_app.auth.pat import PatAuthProvider

__all__ = [
    "AuthProvider",
    "NoAuthProvider",
    "ApiKeyAuthProvider",
    "PatAuthProvider",
    "OAuthAuthProvider",
    "build_auth_provider",
]
