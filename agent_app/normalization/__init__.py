"""Response normalization package.

Converts raw MCP server responses to the standard artifact envelope::

    source_system, artifact_type, stable_id, title, summary, deeplink_url, related[]

Usage::

    from agent_app.normalization import normalize, register_adapter

    normalized = normalize("ado", raw_ado_response)
    register_adapter("my_server", my_adapter_fn)
"""

from agent_app.normalization.normalizer import normalize, register_adapter

__all__ = ["normalize", "register_adapter"]
