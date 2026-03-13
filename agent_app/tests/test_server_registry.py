"""Tests for the MCP server registry."""

import os
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from agent_app.registry.server_registry import (
    ServerRegistry,
    _interpolate,
    _is_write_tool,
    get_registry,
    init_registry,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_registry(servers: list[dict]) -> ServerRegistry:
    """Build a registry directly from a server list (no YAML file needed)."""
    return ServerRegistry(servers)


def _minimal_http_server(label: str = "test", url: str = "http://localhost/api") -> dict:
    return {"label": label, "transport": "http", "url": url, "read_only": True}


def _minimal_stdio_server(
    label: str = "test_stdio",
    command: str = "node",
    args: list[str] | None = None,
) -> dict:
    return {
        "label": label,
        "transport": "stdio",
        "command": command,
        "args": args or ["script.js"],
        "read_only": True,
    }


# ---------------------------------------------------------------------------
# _interpolate
# ---------------------------------------------------------------------------


class TestInterpolate:
    def test_no_placeholders(self) -> None:
        assert _interpolate("http://localhost/api") == "http://localhost/api"

    def test_simple_var_present(self) -> None:
        with patch.dict(os.environ, {"MY_URL": "http://remote/api"}):
            assert _interpolate("${MY_URL}") == "http://remote/api"

    def test_simple_var_missing_returns_empty(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            assert _interpolate("${MISSING_VAR}") == ""

    def test_default_used_when_var_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            assert _interpolate("${MISSING:-http://default}") == "http://default"

    def test_default_not_used_when_var_present(self) -> None:
        with patch.dict(os.environ, {"MY_HOST": "http://actual"}):
            assert _interpolate("${MY_HOST:-http://default}") == "http://actual"

    def test_multiple_placeholders(self) -> None:
        with patch.dict(os.environ, {"A": "foo", "B": "bar"}):
            assert _interpolate("${A}/${B}") == "foo/bar"


# ---------------------------------------------------------------------------
# _is_write_tool
# ---------------------------------------------------------------------------


class TestIsWriteTool:
    @pytest.mark.parametrize(
        "name",
        [
            "create_item",
            "update_work_item",
            "delete_requirement",
            "patch_component",
            "post_event",
            "put_config",
            "insert_record",
            "remove_tag",
            "add_comment",
            "edit_title",
            "write_file",
            "save_document",
            "publish_release",
            "set_status",
            "reset_password",
        ],
    )
    def test_write_tools_detected(self, name: str) -> None:
        assert _is_write_tool(name) is True

    @pytest.mark.parametrize(
        "name",
        [
            "search_requirements",
            "get_requirement",
            "list_related",
            "wit_get_work_item",
            "search_components",
            "get_component",
            "find_requirements_by_work_item",
        ],
    )
    def test_read_tools_not_blocked(self, name: str) -> None:
        assert _is_write_tool(name) is False


# ---------------------------------------------------------------------------
# ServerRegistry construction
# ---------------------------------------------------------------------------


class TestServerRegistry:
    def test_labels_returned(self) -> None:
        registry = _make_registry(
            [_minimal_http_server("jama"), _minimal_http_server("icepanel")]
        )
        assert set(registry.labels()) == {"jama", "icepanel"}

    def test_unknown_label_raises_key_error(self) -> None:
        registry = _make_registry([_minimal_http_server("jama")])
        with pytest.raises(KeyError, match="not registered"):
            registry.get_client("unknown_server")

    def test_is_read_only_default_true(self) -> None:
        # read_only omitted → defaults to True
        registry = _make_registry([{"label": "s", "transport": "http", "url": "http://x"}])
        assert registry.is_read_only("s") is True

    def test_is_read_only_explicit_false(self) -> None:
        registry = _make_registry(
            [{"label": "s", "transport": "http", "url": "http://x", "read_only": False}]
        )
        assert registry.is_read_only("s") is False

    def test_write_tool_blocked_on_read_only_server(self) -> None:
        registry = _make_registry([_minimal_http_server("jama")])
        assert registry.is_tool_allowed("jama", "create_requirement") is False

    def test_read_tool_allowed_on_read_only_server(self) -> None:
        registry = _make_registry([_minimal_http_server("jama")])
        assert registry.is_tool_allowed("jama", "search_requirements") is True

    def test_write_tool_allowed_when_read_only_false(self) -> None:
        registry = _make_registry(
            [{"label": "s", "transport": "http", "url": "http://x", "read_only": False}]
        )
        assert registry.is_tool_allowed("s", "create_item") is True


# ---------------------------------------------------------------------------
# Client construction — HTTP
# ---------------------------------------------------------------------------


class TestHttpClientBuilding:
    def test_builds_mcp_client_for_http(self) -> None:
        from agent_app.mcp_client import MCPClient

        registry = _make_registry([_minimal_http_server("svc", "http://localhost/api")])
        client = registry.get_client("svc")
        assert isinstance(client, MCPClient)
        assert client.base_url == "http://localhost/api"

    def test_client_cached_on_second_access(self) -> None:
        registry = _make_registry([_minimal_http_server("svc")])
        c1 = registry.get_client("svc")
        c2 = registry.get_client("svc")
        assert c1 is c2

    def test_url_env_var_interpolated(self) -> None:
        from agent_app.mcp_client import MCPClient

        with patch.dict(os.environ, {"MY_URL": "http://remote/api"}):
            registry = _make_registry(
                [{"label": "svc", "transport": "http", "url": "${MY_URL}"}]
            )
            client = registry.get_client("svc")
        assert isinstance(client, MCPClient)
        assert client.base_url == "http://remote/api"

    def test_api_key_injected_into_http_client(self) -> None:
        from agent_app.mcp_client import MCPClient

        with patch.dict(os.environ, {"MY_KEY": "test-func-key"}):
            registry = _make_registry(
                [
                    {
                        "label": "svc",
                        "transport": "http",
                        "url": "http://localhost/api",
                        "auth": {
                            "type": "api_key",
                            "header": "x-functions-key",
                            "env_var": "MY_KEY",
                        },
                    }
                ]
            )
            client = registry.get_client("svc")
        assert isinstance(client, MCPClient)
        assert client.function_key == "test-func-key"

    def test_missing_url_raises_value_error(self) -> None:
        registry = _make_registry(
            [{"label": "svc", "transport": "http", "url": ""}]
        )
        with pytest.raises(ValueError, match="url.*required"):
            registry.get_client("svc")


# ---------------------------------------------------------------------------
# Client construction — stdio
# ---------------------------------------------------------------------------


class TestStdioClientBuilding:
    def test_builds_stdio_client(self) -> None:
        from agent_app.mcp_client import StdioMCPClient

        registry = _make_registry([_minimal_stdio_server("ado", "node", ["script.js", "myorg"])])
        client = registry.get_client("ado")
        assert isinstance(client, StdioMCPClient)

    def test_args_env_vars_interpolated(self) -> None:
        from agent_app.mcp_client import StdioMCPClient

        with patch.dict(os.environ, {"MCP_PATH": "/path/to/index.js", "ORG": "myorg"}):
            registry = _make_registry(
                [
                    {
                        "label": "ado",
                        "transport": "stdio",
                        "command": "node",
                        "args": ["${MCP_PATH}", "${ORG}"],
                    }
                ]
            )
            client = registry.get_client("ado")
        assert isinstance(client, StdioMCPClient)
        assert client.args == ["/path/to/index.js", "myorg"]

    def test_pat_auth_args_appended(self) -> None:
        from agent_app.mcp_client import StdioMCPClient

        with patch.dict(os.environ, {"MY_PAT": "token-abc", "MCP_PATH": "index.js", "ORG": "org1"}):
            registry = _make_registry(
                [
                    {
                        "label": "ado",
                        "transport": "stdio",
                        "command": "node",
                        "args": ["${MCP_PATH}", "${ORG}"],
                        "auth": {
                            "type": "pat",
                            "env_var": "MY_PAT",
                            "stdio_auth_flag": "--authentication",
                            "stdio_auth_value": "envvar",
                        },
                    }
                ]
            )
            client = registry.get_client("ado")
        assert isinstance(client, StdioMCPClient)
        # Auth flags appended after positional args
        assert "--authentication" in client.args
        assert "envvar" in client.args


# ---------------------------------------------------------------------------
# from_yaml
# ---------------------------------------------------------------------------


class TestFromYaml:
    def test_loads_from_yaml_file(self, tmp_path: Path) -> None:
        yaml_content = textwrap.dedent(
            """\
            servers:
              - label: demo
                transport: http
                url: "http://localhost/api"
                read_only: true
            """
        )
        config_file = tmp_path / "mcp_servers.yaml"
        config_file.write_text(yaml_content)

        registry = ServerRegistry.from_yaml(config_file)
        assert registry.labels() == ["demo"]

    def test_raises_file_not_found(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing.yaml"
        with pytest.raises(FileNotFoundError):
            ServerRegistry.from_yaml(missing)

    def test_from_yaml_if_exists_returns_none_when_missing(self, tmp_path: Path) -> None:
        result = ServerRegistry.from_yaml_if_exists(tmp_path / "nope.yaml")
        assert result is None

    def test_from_yaml_if_exists_loads_when_present(self, tmp_path: Path) -> None:
        yaml_content = "servers:\n  - label: x\n    transport: http\n    url: http://x\n"
        config_file = tmp_path / "mcp_servers.yaml"
        config_file.write_text(yaml_content)

        result = ServerRegistry.from_yaml_if_exists(config_file)
        assert result is not None
        assert "x" in result.labels()


# ---------------------------------------------------------------------------
# Module-level singleton (init_registry / get_registry)
# ---------------------------------------------------------------------------


class TestRegistrySingleton:
    def test_init_registry_returns_registry(self, tmp_path: Path) -> None:
        import agent_app.registry.server_registry as sr_module

        prev = sr_module._REGISTRY
        try:
            yaml_content = "servers:\n  - label: s\n    transport: http\n    url: http://s\n"
            config_file = tmp_path / "mcp_servers.yaml"
            config_file.write_text(yaml_content)

            reg = init_registry(config_file)
            assert reg.labels() == ["s"]
            assert get_registry() is reg
        finally:
            sr_module._REGISTRY = prev
