"""Standard MCP response envelope.

All MCP servers MUST use this format per repo standards.
"""

from typing import Any


def create_mcp_response(
    source_system: str,
    artifact_type: str,
    stable_id: str | None = None,
    title: str | None = None,
    summary: str | None = None,
    deeplink_url: str | None = None,
    related: list[dict[str, Any]] | None = None,
    data: dict[str, Any] | None = None,
    error: str | None = None,
    found: bool = True,
) -> dict[str, Any]:
    """Create standardized MCP response envelope.

    Args:
        source_system: Source system name (JAMA, Azure DevOps, IcePanel)
        artifact_type: Type of artifact (requirement, work_item, component)
        stable_id: Unique artifact identifier
        title: Artifact title
        summary: Brief artifact summary
        deeplink_url: URL to view artifact in source system
        related: List of related artifact references
        data: Full artifact data (optional)
        error: Error message if operation failed
        found: Whether artifact was found

    Returns:
        Standardized MCP response dictionary
    """
    response = {
        "source_system": source_system,
        "artifact_type": artifact_type,
        "found": found,
    }

    if stable_id:
        response["stable_id"] = stable_id
    if title:
        response["title"] = title
    if summary:
        response["summary"] = summary
    if deeplink_url:
        response["deeplink_url"] = deeplink_url
    if related:
        response["related"] = related
    if data:
        response["data"] = data
    if error:
        response["error"] = error

    return response


def create_search_response(
    source_system: str,
    artifact_type: str,
    query: str,
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Create standardized search response.

    Args:
        source_system: Source system name
        artifact_type: Type of artifact being searched
        query: Search query string
        results: List of matching artifacts

    Returns:
        Standardized search response dictionary
    """
    return {
        "source_system": source_system,
        "artifact_type": artifact_type,
        "query": query,
        "count": len(results),
        "results": results,
    }
