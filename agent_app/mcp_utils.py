"""Utilities for parallel MCP tool execution."""

import asyncio
import logging
from typing import Any

from agent_app.mcp_client import get_mcp_client

logger = logging.getLogger(__name__)


async def fetch_artifact_batch(
    server_name: str, tool_name: str, artifact_ids: list[str]
) -> list[dict[str, Any]]:
    """
    Fetch multiple artifacts from a single MCP server in parallel.

    Args:
        server_name: MCP server name (jama, ado, icepanel)
        tool_name: Tool to call (e.g., get_requirement, get_work_item)
        artifact_ids: List of artifact IDs to fetch

    Returns:
        List of artifact dictionaries (empty dict if fetch failed)
    """
    if not artifact_ids:
        return []

    client = get_mcp_client(server_name)

    async def fetch_one(artifact_id: str) -> dict[str, Any]:
        try:
            if server_name == "ado":
                # ADO needs project parameter
                result = await asyncio.to_thread(
                    client.call_tool,
                    tool_name,
                    {"work_item_id": artifact_id, "project": "DemoProject"},
                )
            else:
                # JAMA/IcePanel use standard parameter name
                param_name = (
                    "requirement_id" if server_name == "jama" else "component_id"
                )
                result = await asyncio.to_thread(
                    client.call_tool, tool_name, {param_name: artifact_id}
                )

            return result if result else {}
        except Exception as e:
            logger.warning(
                f"Failed to fetch {artifact_id} from {server_name}: {e}",
                exc_info=True,
            )
            return {}

    # Execute all fetches concurrently
    results = await asyncio.gather(*[fetch_one(aid) for aid in artifact_ids])
    return [r for r in results if r]  # Filter out empty results


async def fetch_related_artifacts_parallel(
    base_artifact: dict[str, Any],
) -> dict[str, Any]:
    """
    Fetch all related artifacts from multiple MCP servers in parallel.

    Args:
        base_artifact: The source artifact with 'related' array

    Returns:
        Dictionary with source artifact and related artifacts grouped by system
    """
    if "related" not in base_artifact:
        return {
            "source_artifact": base_artifact,
            "related_artifacts": [],
            "errors": [],
        }

    # Group related IDs by system
    jama_ids = []
    ado_ids = []
    icepanel_ids = []

    for rel in base_artifact.get("related", []):
        system = rel.get("system", "").upper()
        artifact_id = rel.get("id", "")

        if system == "JAMA":
            jama_ids.append(artifact_id)
        elif system == "ADO":
            ado_ids.append(artifact_id)
        elif system == "ICEPANEL":
            icepanel_ids.append(artifact_id)

    logger.info(
        f"Fetching related artifacts: {len(jama_ids)} JAMA, "
        f"{len(ado_ids)} ADO, {len(icepanel_ids)} IcePanel"
    )

    # Fan out concurrent requests to all systems
    results = await asyncio.gather(
        fetch_artifact_batch("jama", "get_requirement", jama_ids),
        fetch_artifact_batch("ado", "wit_get_work_item", ado_ids),
        fetch_artifact_batch("icepanel", "get_component", icepanel_ids),
        return_exceptions=True,  # Don't fail entire query if one system is down
    )

    # Unpack results and track expected vs actual counts for error detection
    jama_results = results[0] if not isinstance(results[0], Exception) else []
    ado_results = results[1] if not isinstance(results[1], Exception) else []
    icepanel_results = results[2] if not isinstance(results[2], Exception) else []

    # Collect errors (both exceptions and partial failures)
    errors = []
    for i, result in enumerate(results):
        system_name = ["JAMA", "ADO", "IcePanel"][i]
        expected_count = [len(jama_ids), len(ado_ids), len(icepanel_ids)][i]

        if isinstance(result, Exception):
            errors.append({"system": system_name, "error": str(result)})
            logger.error(f"Failed to fetch {system_name} artifacts: {result}")
        elif expected_count > 0 and len(result) < expected_count:
            # Partial failure - some artifacts failed to fetch
            errors.append({
                "system": system_name,
                "error": f"Partial failure: fetched {len(result)}/{expected_count} artifacts"
            })
            logger.warning(
                f"{system_name} partial failure: fetched {len(result)}/{expected_count}"
            )

    # Merge all results
    all_related = []
    if isinstance(jama_results, list):
        all_related.extend(jama_results)
    if isinstance(ado_results, list):
        all_related.extend(ado_results)
    if isinstance(icepanel_results, list):
        all_related.extend(icepanel_results)

    return {
        "source_artifact": base_artifact,
        "related_artifacts": all_related,
        "counts": {
            "jama": len(jama_results) if isinstance(jama_results, list) else 0,
            "ado": len(ado_results) if isinstance(ado_results, list) else 0,
            "icepanel": (
                len(icepanel_results) if isinstance(icepanel_results, list) else 0
            ),
        },
        "errors": errors,
    }
