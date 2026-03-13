"""Tests for auth provider implementations."""

import os
from unittest.mock import patch

import pytest

from agent_app.auth.api_key import ApiKeyAuthProvider
from agent_app.auth.factory import build_auth_provider
from agent_app.auth.none_provider import NoAuthProvider
from agent_app.auth.oauth import OAuthAuthProvider
from agent_app.auth.pat import PatAuthProvider


class TestNoAuthProvider:
    """NoAuthProvider always returns empty dicts/lists."""

    def test_get_headers_empty(self) -> None:
        provider = NoAuthProvider()
        assert provider.get_headers() == {}

    def test_get_env_vars_empty(self) -> None:
        provider = NoAuthProvider()
        assert provider.get_env_vars() == {}

    def test_get_stdio_args_empty(self) -> None:
        provider = NoAuthProvider()
        assert provider.get_stdio_args() == []


class TestApiKeyAuthProvider:
    """ApiKeyAuthProvider injects the key as an HTTP header."""

    def test_header_present_when_env_var_set(self) -> None:
        with patch.dict(os.environ, {"MY_KEY": "secret-key-123"}):
            provider = ApiKeyAuthProvider(header="x-functions-key", env_var="MY_KEY")
        assert provider.get_headers() == {"x-functions-key": "secret-key-123"}

    def test_empty_headers_when_env_var_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            provider = ApiKeyAuthProvider(header="x-functions-key", env_var="MISSING_KEY")
        assert provider.get_headers() == {}

    def test_env_vars_empty(self) -> None:
        with patch.dict(os.environ, {"MY_KEY": "k"}):
            provider = ApiKeyAuthProvider(header="x-api-key", env_var="MY_KEY")
        assert provider.get_env_vars() == {}

    def test_stdio_args_empty(self) -> None:
        with patch.dict(os.environ, {"MY_KEY": "k"}):
            provider = ApiKeyAuthProvider(header="x-api-key", env_var="MY_KEY")
        assert provider.get_stdio_args() == []


class TestPatAuthProvider:
    """PatAuthProvider handles both HTTP and stdio transport modes."""

    def test_http_bearer_header_when_token_set(self) -> None:
        with patch.dict(os.environ, {"MY_PAT": "pat-token-xyz"}):
            provider = PatAuthProvider(env_var="MY_PAT")
        assert provider.get_headers() == {"Authorization": "Bearer pat-token-xyz"}

    def test_empty_headers_when_token_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            provider = PatAuthProvider(env_var="MISSING_PAT")
        assert provider.get_headers() == {}

    def test_env_var_injected_for_stdio(self) -> None:
        with patch.dict(os.environ, {"ADO_PAT": "ado-token"}):
            provider = PatAuthProvider(env_var="ADO_PAT")
        assert provider.get_env_vars() == {"ADO_PAT": "ado-token"}

    def test_stdio_args_with_flag_when_token_set(self) -> None:
        with patch.dict(os.environ, {"ADO_PAT": "ado-token"}):
            provider = PatAuthProvider(
                env_var="ADO_PAT",
                stdio_auth_flag="--authentication",
                stdio_auth_value="envvar",
            )
        assert provider.get_stdio_args() == ["--authentication", "envvar"]

    def test_stdio_args_empty_when_token_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            provider = PatAuthProvider(
                env_var="MISSING_PAT",
                stdio_auth_flag="--authentication",
                stdio_auth_value="envvar",
            )
        assert provider.get_stdio_args() == []

    def test_stdio_args_empty_when_no_flag_configured(self) -> None:
        with patch.dict(os.environ, {"ADO_PAT": "ado-token"}):
            provider = PatAuthProvider(env_var="ADO_PAT")  # no stdio_auth_flag
        assert provider.get_stdio_args() == []


class TestOAuthAuthProvider:
    """OAuthAuthProvider stub — always returns empty credentials."""

    def test_get_headers_empty(self) -> None:
        provider = OAuthAuthProvider(tenant_id="tenant-123", client_id="app-456")
        assert provider.get_headers() == {}

    def test_get_env_vars_empty(self) -> None:
        provider = OAuthAuthProvider()
        assert provider.get_env_vars() == {}

    def test_get_stdio_args_empty(self) -> None:
        provider = OAuthAuthProvider()
        assert provider.get_stdio_args() == []


class TestBuildAuthProvider:
    """Factory creates the correct provider from a config dict."""

    def test_none_type_returns_no_auth(self) -> None:
        provider = build_auth_provider({"type": "none"})
        assert isinstance(provider, NoAuthProvider)

    def test_empty_config_returns_no_auth(self) -> None:
        provider = build_auth_provider(None)
        assert isinstance(provider, NoAuthProvider)

    def test_empty_dict_returns_no_auth(self) -> None:
        provider = build_auth_provider({})
        assert isinstance(provider, NoAuthProvider)

    def test_api_key_type(self) -> None:
        with patch.dict(os.environ, {"MY_KEY": "val"}):
            provider = build_auth_provider(
                {"type": "api_key", "header": "x-functions-key", "env_var": "MY_KEY"}
            )
        assert isinstance(provider, ApiKeyAuthProvider)
        assert provider.get_headers() == {"x-functions-key": "val"}

    def test_pat_type(self) -> None:
        with patch.dict(os.environ, {"MY_PAT": "tok"}):
            provider = build_auth_provider(
                {
                    "type": "pat",
                    "env_var": "MY_PAT",
                    "stdio_auth_flag": "--auth",
                    "stdio_auth_value": "envvar",
                }
            )
        assert isinstance(provider, PatAuthProvider)
        assert provider.get_env_vars() == {"MY_PAT": "tok"}
        assert provider.get_stdio_args() == ["--auth", "envvar"]

    def test_oauth_type_returns_stub(self) -> None:
        provider = build_auth_provider(
            {"type": "oauth", "tenant_id": "t1", "client_id": "c1"}
        )
        assert isinstance(provider, OAuthAuthProvider)
        assert provider.get_headers() == {}

    def test_unknown_type_falls_back_to_no_auth(self) -> None:
        provider = build_auth_provider({"type": "magic_auth"})
        assert isinstance(provider, NoAuthProvider)
