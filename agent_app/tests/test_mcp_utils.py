"""Tests for parallel MCP execution utilities."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_app.mcp_utils import fetch_artifact_batch, fetch_related_artifacts_parallel


@pytest.mark.asyncio
async def test_fetch_artifact_batch_success():
    """Test successful parallel fetch of artifacts."""
    mock_client = MagicMock()
    mock_client.call_tool.return_value = {
        "id": "REQ-001",
        "title": "Test Requirement",
        "deeplink_url": "https://demo-viewer.example.com/jama/REQ-001",
    }

    with patch("agent_app.mcp_utils.get_mcp_client", return_value=mock_client):
        results = await fetch_artifact_batch(
            "jama", "get_requirement", ["REQ-001", "REQ-002"]
        )

    assert len(results) == 2
    assert all(r.get("id") for r in results)


@pytest.mark.asyncio
async def test_fetch_artifact_batch_partial_failure():
    """Test that partial failures don't break entire batch."""
    mock_client = MagicMock()

    def side_effect(tool_name, params):
        if params.get("requirement_id") == "REQ-001":
            return {"id": "REQ-001", "title": "Test"}
        raise Exception("Simulated failure")

    mock_client.call_tool.side_effect = side_effect

    with patch("agent_app.mcp_utils.get_mcp_client", return_value=mock_client):
        results = await fetch_artifact_batch(
            "jama", "get_requirement", ["REQ-001", "REQ-002"]
        )

    # Should get 1 success, 1 failure (filtered out)
    assert len(results) == 1
    assert results[0]["id"] == "REQ-001"


@pytest.mark.asyncio
async def test_fetch_artifact_batch_empty_list():
    """Test that empty artifact list returns empty results."""
    results = await fetch_artifact_batch("jama", "get_requirement", [])
    assert results == []


@pytest.mark.asyncio
async def test_fetch_related_artifacts_parallel():
    """Test parallel fetching of related artifacts from multiple systems."""
    base_artifact = {
        "id": "REQ-001",
        "title": "Test Requirement",
        "related": [
            {"id": "REQ-002", "system": "JAMA"},
            {"id": "7", "system": "ADO"},
            {"id": "COMP-201", "system": "IcePanel"},
        ],
    }

    mock_jama_client = MagicMock()
    mock_jama_client.call_tool.return_value = {
        "id": "REQ-002",
        "title": "Related Requirement",
    }

    mock_ado_client = MagicMock()
    mock_ado_client.call_tool.return_value = {"id": "7", "title": "User Story"}

    mock_icepanel_client = MagicMock()
    mock_icepanel_client.call_tool.return_value = {
        "id": "COMP-201",
        "title": "Auth Service",
    }

    def get_client(server_name):
        if server_name == "jama":
            return mock_jama_client
        elif server_name == "ado":
            return mock_ado_client
        elif server_name == "icepanel":
            return mock_icepanel_client

    with patch("agent_app.mcp_utils.get_mcp_client", side_effect=get_client):
        result = await fetch_related_artifacts_parallel(base_artifact)

    assert result["source_artifact"]["id"] == "REQ-001"
    assert len(result["related_artifacts"]) == 3
    assert result["counts"]["jama"] == 1
    assert result["counts"]["ado"] == 1
    assert result["counts"]["icepanel"] == 1
    assert len(result["errors"]) == 0


@pytest.mark.asyncio
async def test_fetch_related_artifacts_with_system_failure():
    """Test that one system failure doesn't break entire query."""
    base_artifact = {
        "id": "REQ-001",
        "title": "Test Requirement",
        "related": [
            {"id": "REQ-002", "system": "JAMA"},
            {"id": "7", "system": "ADO"},
        ],
    }

    mock_jama_client = MagicMock()
    mock_jama_client.call_tool.return_value = {
        "id": "REQ-002",
        "title": "Related Requirement",
    }

    mock_ado_client = MagicMock()
    mock_ado_client.call_tool.side_effect = Exception("ADO service down")

    def get_client(server_name):
        if server_name == "jama":
            return mock_jama_client
        elif server_name == "ado":
            return mock_ado_client
        elif server_name == "icepanel":
            return MagicMock()

    with patch("agent_app.mcp_utils.get_mcp_client", side_effect=get_client):
        result = await fetch_related_artifacts_parallel(base_artifact)

    # Should get JAMA results even though ADO failed
    assert len(result["related_artifacts"]) >= 1
    assert any(r["id"] == "REQ-002" for r in result["related_artifacts"])
    # Should track error
    assert any(e["system"] == "ADO" for e in result["errors"])


@pytest.mark.asyncio
async def test_fetch_related_artifacts_no_related():
    """Test artifact with no related items."""
    base_artifact = {"id": "REQ-001", "title": "Test Requirement"}

    result = await fetch_related_artifacts_parallel(base_artifact)

    assert result["source_artifact"]["id"] == "REQ-001"
    assert result["related_artifacts"] == []
    assert result["errors"] == []
