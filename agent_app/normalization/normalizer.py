"""Response normalization — converts MCP tool output to the standard envelope.

All MCP servers (official or custom) should return data in the standard envelope::

    {
        "source_system":  str,   # e.g., "JAMA", "Azure DevOps", "IcePanel"
        "artifact_type":  str,   # e.g., "requirement", "work_item", "component"
        "stable_id":      str,   # stable, system-specific identifier
        "title":          str,
        "summary":        str,
        "deeplink_url":   str,
        "related":        list[dict]  # [{id, type, system, title}, ...]
    }

Official MCP servers (e.g., the Azure DevOps MCP) return data in their own
schema. Thin adapter functions registered here convert those responses to the
standard envelope so the rest of the agent code sees a consistent shape.

Built-in adapters:
- ``identity``   — pass-through for servers that already emit the envelope.
- ``ado_work_item`` — maps ADO work item fields to the standard envelope.

Customers can register their own adapters::

    from agent_app.normalization import normalizer
    normalizer.register_adapter("my_server", my_adapter_fn)

Where ``my_adapter_fn(raw: dict) -> dict`` maps the raw response fields.
"""

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Type alias for adapter callables
AdapterFn = Callable[[dict[str, Any]], dict[str, Any]]

# Standard envelope required keys (used for conformance check)
_ENVELOPE_KEYS = {"source_system", "artifact_type"}


def _is_standard_envelope(response: dict[str, Any]) -> bool:
    """Return True if the response already conforms to the standard envelope."""
    return _ENVELOPE_KEYS.issubset(response.keys())


# ---------------------------------------------------------------------------
# Built-in adapters
# ---------------------------------------------------------------------------


def identity_adapter(raw: dict[str, Any]) -> dict[str, Any]:
    """Pass-through adapter — the response is already standard.

    Used for demo servers (JAMA, IcePanel in this PoC) which produce
    the envelope directly via mcp_response.py.
    """
    return raw


def ado_work_item_adapter(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize an Azure DevOps work item response to the standard envelope.

    The official ADO MCP server returns work items with ADO-specific field
    names. This adapter maps them to the envelope so agent tools receive
    consistent output regardless of whether they called the demo server or
    the official ADO MCP.

    Args:
        raw: Raw response from the ADO MCP server.

    Returns:
        Standard envelope dict.
    """
    # If already normalized, return as-is
    if _is_standard_envelope(raw):
        return raw

    fields = raw.get("fields", raw)  # ADO wraps fields under 'fields' key

    # Derive a stable ID: prefer "System.Id", fall back to top-level "id"
    work_item_id = str(
        fields.get("System.Id") or raw.get("id") or raw.get("work_item_id", "")
    )
    stable_id = f"WI-{work_item_id}" if work_item_id and not work_item_id.startswith("WI-") else work_item_id

    title = (
        fields.get("System.Title")
        or raw.get("title")
        or raw.get("name")
        or ""
    )
    state = fields.get("System.State") or raw.get("state", "")
    work_item_type = fields.get("System.WorkItemType") or raw.get("type", "work_item")
    description = (
        fields.get("System.Description")
        or raw.get("description")
        or raw.get("summary")
        or ""
    )

    # Deep link — prefer _links.html.href, fall back to url/deeplink fields
    deeplink = (
        raw.get("_links", {}).get("html", {}).get("href")
        or raw.get("deeplink_url")
        or raw.get("url")
        or ""
    )

    normalized: dict[str, Any] = {
        "source_system": "Azure DevOps",
        "artifact_type": work_item_type.lower().replace(" ", "_"),
        "stable_id": stable_id,
        "title": title,
        "summary": f"[{state}] {description[:200]}" if description else f"[{state}]",
        "deeplink_url": deeplink,
        "related": raw.get("related", []),
    }

    # Preserve any extra fields from the original response
    normalized["_raw"] = raw
    return normalized


# ---------------------------------------------------------------------------
# Adapter registry
# ---------------------------------------------------------------------------

# label → adapter function. "identity" catches all labels not explicitly mapped.
_ADAPTERS: dict[str, AdapterFn] = {
    "identity": identity_adapter,
    "ado_work_item": ado_work_item_adapter,
    # The demo servers already produce the standard envelope — identity is fine.
    "jama": identity_adapter,
    "icepanel": identity_adapter,
    # ADO: use ado_work_item adapter since the official MCP has its own schema.
    "ado": ado_work_item_adapter,
}


def register_adapter(label: str, adapter_fn: AdapterFn) -> None:
    """Register a custom response adapter for a server label.

    Call this during app startup before any tool calls are made::

        from agent_app.normalization.normalizer import register_adapter

        def my_server_adapter(raw: dict) -> dict:
            return {
                "source_system": "My System",
                "artifact_type": raw.get("kind", "item"),
                "stable_id": raw["id"],
                "title": raw["name"],
                "summary": raw.get("desc", ""),
                "deeplink_url": f"https://my-system.example.com/items/{raw['id']}",
                "related": [],
            }

        register_adapter("my_server", my_server_adapter)

    Args:
        label: Server label matching the entry in mcp_servers.yaml.
        adapter_fn: Callable that maps raw dict → standard envelope dict.
    """
    _ADAPTERS[label] = adapter_fn
    logger.debug("Normalizer: registered adapter for server label '%s'", label)


def normalize(label: str, raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize a raw MCP tool response to the standard envelope.

    Looks up the adapter for ``label``. If no adapter is registered, applies
    a best-effort auto-normalization before logging a debug notice.

    Args:
        label: Server label (e.g., "ado", "jama", "my_server").
        raw: Raw response dict from the MCP server.

    Returns:
        Standard envelope dict (may include a ``_raw`` key with original data).
    """
    if not isinstance(raw, dict):
        logger.warning(
            "Normalizer: expected dict response from '%s', got %s. Wrapping.",
            label,
            type(raw).__name__,
        )
        return {
            "source_system": label,
            "artifact_type": "unknown",
            "stable_id": "",
            "title": "",
            "summary": str(raw),
            "deeplink_url": "",
            "related": [],
        }

    adapter = _ADAPTERS.get(label)
    if adapter is not None:
        return adapter(raw)

    # No adapter registered — auto-normalize if not already an envelope
    if _is_standard_envelope(raw):
        return raw

    logger.debug(
        "Normalizer: no adapter for '%s'; applying best-effort normalization. "
        "Register a custom adapter via register_adapter('%s', fn) for accuracy.",
        label,
        label,
    )
    return _auto_normalize(label, raw)


def _auto_normalize(label: str, raw: dict[str, Any]) -> dict[str, Any]:
    """Best-effort normalization for servers without a registered adapter.

    Maps common field names used by various REST APIs to the standard envelope.
    This is intentionally conservative — register a custom adapter for accuracy.
    """
    stable_id = str(raw.get("id") or raw.get("stable_id") or raw.get("key") or "")
    title = (
        raw.get("title")
        or raw.get("name")
        or raw.get("summary")
        or raw.get("subject")
        or ""
    )
    summary = (
        raw.get("description")
        or raw.get("summary")
        or raw.get("body")
        or raw.get("content")
        or ""
    )
    deeplink = (
        raw.get("deeplink_url")
        or raw.get("url")
        or raw.get("web_url")
        or raw.get("html_url")
        or ""
    )

    result: dict[str, Any] = {
        "source_system": label,
        "artifact_type": raw.get("artifact_type") or raw.get("type") or "item",
        "stable_id": stable_id,
        "title": str(title),
        "summary": str(summary)[:300],
        "deeplink_url": str(deeplink),
        "related": raw.get("related", []),
        "_raw": raw,
    }
    return result
