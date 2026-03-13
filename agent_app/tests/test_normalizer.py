"""Tests for response normalization."""

from typing import Any

import pytest

from agent_app.normalization.normalizer import (
    _auto_normalize,
    _is_standard_envelope,
    identity_adapter,
    normalize,
    register_adapter,
    ado_work_item_adapter,
)


class TestIsStandardEnvelope:
    def test_conforming_response(self) -> None:
        resp = {
            "source_system": "JAMA",
            "artifact_type": "requirement",
            "stable_id": "REQ-001",
            "title": "Auth",
        }
        assert _is_standard_envelope(resp) is True

    def test_missing_source_system(self) -> None:
        resp = {"artifact_type": "requirement"}
        assert _is_standard_envelope(resp) is False

    def test_missing_artifact_type(self) -> None:
        resp = {"source_system": "JAMA"}
        assert _is_standard_envelope(resp) is False

    def test_empty_dict(self) -> None:
        assert _is_standard_envelope({}) is False


class TestIdentityAdapter:
    def test_passes_through_unchanged(self) -> None:
        resp = {"source_system": "JAMA", "artifact_type": "requirement", "title": "T"}
        assert identity_adapter(resp) is resp


class TestAdoWorkItemAdapter:
    """Adapter should map ADO-specific fields to the standard envelope."""

    def _ado_raw(self, work_item_id: str = "42", title: str = "Login bug") -> dict[str, Any]:
        return {
            "id": work_item_id,
            "fields": {
                "System.Id": work_item_id,
                "System.Title": title,
                "System.State": "Active",
                "System.WorkItemType": "Bug",
                "System.Description": "Something is broken",
            },
            "_links": {"html": {"href": "https://dev.azure.com/org/proj/_workitems/42"}},
        }

    def test_maps_to_standard_envelope(self) -> None:
        result = ado_work_item_adapter(self._ado_raw())
        assert result["source_system"] == "Azure DevOps"
        assert result["artifact_type"] == "bug"
        assert result["stable_id"] == "WI-42"
        assert result["title"] == "Login bug"
        assert "Active" in result["summary"]
        assert result["deeplink_url"] == "https://dev.azure.com/org/proj/_workitems/42"

    def test_already_normalized_passes_through(self) -> None:
        already = {
            "source_system": "Azure DevOps",
            "artifact_type": "work_item",
            "stable_id": "WI-5",
            "title": "T",
        }
        result = ado_work_item_adapter(already)
        assert result is already

    def test_raw_preserved_in_output(self) -> None:
        raw = self._ado_raw("7")
        result = ado_work_item_adapter(raw)
        assert "_raw" in result


class TestNormalize:
    """normalize() dispatches to the correct adapter by label."""

    def test_jama_uses_identity(self) -> None:
        resp = {
            "source_system": "JAMA",
            "artifact_type": "requirement",
            "stable_id": "REQ-001",
            "title": "T",
        }
        result = normalize("jama", resp)
        assert result is resp  # identity returns same object

    def test_ado_uses_ado_adapter(self) -> None:
        raw = {
            "id": "10",
            "fields": {
                "System.Id": "10",
                "System.Title": "Sprint task",
                "System.State": "New",
                "System.WorkItemType": "Task",
            },
        }
        result = normalize("ado", raw)
        assert result["source_system"] == "Azure DevOps"
        assert result["stable_id"] == "WI-10"

    def test_custom_adapter_registered_and_used(self) -> None:
        def my_adapter(raw: dict) -> dict:
            return {
                "source_system": "MySystem",
                "artifact_type": "ticket",
                "stable_id": raw.get("ticket_id", ""),
                "title": raw.get("subject", ""),
                "summary": "",
                "deeplink_url": "",
                "related": [],
            }

        register_adapter("my_system", my_adapter)
        raw = {"ticket_id": "T-99", "subject": "Custom thing"}
        result = normalize("my_system", raw)
        assert result["source_system"] == "MySystem"
        assert result["stable_id"] == "T-99"

    def test_non_dict_response_wrapped(self) -> None:
        result = normalize("unknown_server", "not a dict")  # type: ignore[arg-type]
        assert result["source_system"] == "unknown_server"
        assert result["artifact_type"] == "unknown"

    def test_auto_normalize_for_unregistered_label(self) -> None:
        raw = {
            "id": "X-1",
            "title": "Something",
            "description": "A description",
            "url": "https://example.com/X-1",
        }
        result = normalize("brand_new_server", raw)
        assert result["stable_id"] == "X-1"
        assert result["title"] == "Something"
        assert result["deeplink_url"] == "https://example.com/X-1"


class TestAutoNormalize:
    def test_maps_common_field_names(self) -> None:
        raw = {
            "id": "42",
            "name": "Widget",
            "description": "A widget",
            "url": "https://example.com/42",
        }
        result = _auto_normalize("some_server", raw)
        assert result["stable_id"] == "42"
        assert result["title"] == "Widget"
        assert "A widget" in result["summary"]
        assert result["deeplink_url"] == "https://example.com/42"

    def test_related_preserved(self) -> None:
        raw = {"id": "1", "related": [{"id": "2", "system": "OTHER"}]}
        result = _auto_normalize("svc", raw)
        assert result["related"] == [{"id": "2", "system": "OTHER"}]

    def test_raw_preserved_in_output(self) -> None:
        raw = {"id": "1"}
        result = _auto_normalize("svc", raw)
        assert result["_raw"] is raw

    def test_summary_truncated_to_300_chars(self) -> None:
        raw = {"id": "1", "description": "x" * 500}
        result = _auto_normalize("svc", raw)
        assert len(result["summary"]) <= 300
