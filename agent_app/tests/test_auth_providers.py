"""Tests for auth provider implementations."""

import os
from unittest.mock import MagicMock, patch

import pytest

from agent_app.auth.api_key import ApiKeyAuthProvider
from agent_app.auth.azure_identity_provider import AzureIdentityAuthProvider
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

    def test_validate_passes_when_key_set(self) -> None:
        with patch.dict(os.environ, {"MY_KEY": "k"}):
            provider = ApiKeyAuthProvider(header="x-api-key", env_var="MY_KEY")
        assert provider.validate() == []

    def test_validate_fails_when_key_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            provider = ApiKeyAuthProvider(header="x-api-key", env_var="MISSING")
        assert len(provider.validate()) == 1


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

    def test_validate_passes_when_token_set(self) -> None:
        with patch.dict(os.environ, {"MY_PAT": "tok"}):
            provider = PatAuthProvider(env_var="MY_PAT")
        assert provider.validate() == []

    def test_validate_fails_when_token_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            provider = PatAuthProvider(env_var="MISSING")
        issues = provider.validate()
        assert len(issues) == 1
        assert "MISSING" in issues[0]


class TestOAuthAuthProvider:
    """OAuthAuthProvider — MSAL-based token acquisition."""

    def test_empty_headers_when_msal_not_available(self) -> None:
        with patch("agent_app.auth.oauth._MSAL_AVAILABLE", False):
            provider = OAuthAuthProvider(
                tenant_id="t1", client_id="c1", scopes=["s1"]
            )
            assert provider.get_headers() == {}

    def test_empty_headers_when_client_id_missing(self) -> None:
        provider = OAuthAuthProvider(tenant_id="t1", client_id="")
        assert provider.get_headers() == {}

    def test_get_env_vars_empty(self) -> None:
        provider = OAuthAuthProvider()
        assert provider.get_env_vars() == {}

    def test_get_stdio_args_empty(self) -> None:
        provider = OAuthAuthProvider()
        assert provider.get_stdio_args() == []

    def test_confidential_client_token_acquisition(self) -> None:
        """Confidential client acquires token via client credentials."""
        mock_app = MagicMock()
        mock_app.get_accounts.return_value = []
        mock_app.acquire_token_for_client.return_value = {
            "access_token": "mock-access-token"
        }

        with patch.dict(os.environ, {"MY_SECRET": "secret-value"}):
            provider = OAuthAuthProvider(
                tenant_id="t1",
                client_id="c1",
                scopes=["https://graph.microsoft.com/.default"],
                client_secret_env_var="MY_SECRET",
            )

        with patch("agent_app.auth.oauth._MSAL_AVAILABLE", True):
            provider._app = mock_app
            headers = provider.get_headers()

        assert headers == {"Authorization": "Bearer mock-access-token"}

    def test_silent_token_acquisition_from_cache(self) -> None:
        """Silent acquisition returns cached token."""
        mock_account = MagicMock()
        mock_app = MagicMock()
        mock_app.get_accounts.return_value = [mock_account]
        mock_app.acquire_token_silent.return_value = {
            "access_token": "cached-token"
        }

        provider = OAuthAuthProvider(
            tenant_id="t1", client_id="c1", scopes=["s1"]
        )
        with patch("agent_app.auth.oauth._MSAL_AVAILABLE", True):
            provider._app = mock_app
            headers = provider.get_headers()

        assert headers == {"Authorization": "Bearer cached-token"}
        mock_app.acquire_token_silent.assert_called_once()

    def test_failed_token_returns_empty_headers(self) -> None:
        """Failed token acquisition returns empty headers."""
        mock_app = MagicMock()
        mock_app.get_accounts.return_value = []
        mock_app.acquire_token_interactive.return_value = {
            "error": "auth_failed",
            "error_description": "User cancelled",
        }

        provider = OAuthAuthProvider(
            tenant_id="t1", client_id="c1", scopes=["s1"]
        )
        with patch("agent_app.auth.oauth._MSAL_AVAILABLE", True):
            provider._app = mock_app
            headers = provider.get_headers()

        assert headers == {}

    def test_validate_passes_with_valid_config(self) -> None:
        with patch("agent_app.auth.oauth._MSAL_AVAILABLE", True):
            with patch.dict(os.environ, {"SECRET": "val"}):
                provider = OAuthAuthProvider(
                    tenant_id="t1",
                    client_id="c1",
                    scopes=["s1"],
                    client_secret_env_var="SECRET",
                )
        assert provider.validate() == []

    def test_validate_reports_missing_msal(self) -> None:
        with patch("agent_app.auth.oauth._MSAL_AVAILABLE", False):
            provider = OAuthAuthProvider(client_id="c1")
            issues = provider.validate()
        assert any("msal" in i for i in issues)

    def test_validate_reports_missing_client_id(self) -> None:
        provider = OAuthAuthProvider(client_id="")
        issues = provider.validate()
        assert any("client_id" in i for i in issues)

    def test_validate_reports_missing_secret_env_var(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            provider = OAuthAuthProvider(
                client_id="c1", client_secret_env_var="MISSING_SECRET"
            )
        issues = provider.validate()
        assert any("MISSING_SECRET" in i for i in issues)


class TestAzureIdentityAuthProvider:
    """AzureIdentityAuthProvider uses DefaultAzureCredential."""

    def test_empty_headers_when_azure_identity_not_available(self) -> None:
        with patch(
            "agent_app.auth.azure_identity_provider._AZURE_IDENTITY_AVAILABLE", False
        ):
            provider = AzureIdentityAuthProvider(scopes=["https://x/.default"])
        assert provider.get_headers() == {}

    def test_empty_headers_when_no_scopes(self) -> None:
        provider = AzureIdentityAuthProvider(scopes=[])
        assert provider.get_headers() == {}

    def test_get_env_vars_empty(self) -> None:
        provider = AzureIdentityAuthProvider(scopes=["s1"])
        assert provider.get_env_vars() == {}

    def test_get_stdio_args_empty(self) -> None:
        provider = AzureIdentityAuthProvider(scopes=["s1"])
        assert provider.get_stdio_args() == []

    def test_bearer_header_with_mock_credential(self) -> None:
        """Successful token acquisition returns Bearer header."""
        mock_credential = MagicMock()
        mock_token = MagicMock()
        mock_token.token = "azure-access-token"
        mock_credential.get_token.return_value = mock_token

        with patch(
            "agent_app.auth.azure_identity_provider._AZURE_IDENTITY_AVAILABLE", True
        ):
            provider = AzureIdentityAuthProvider(
                scopes=["https://management.azure.com/.default"]
            )
            provider._credential = mock_credential
            headers = provider.get_headers()

        assert headers == {"Authorization": "Bearer azure-access-token"}
        mock_credential.get_token.assert_called_once_with(
            "https://management.azure.com/.default"
        )

    def test_empty_headers_on_credential_failure(self) -> None:
        """Failed credential returns empty headers."""
        mock_credential = MagicMock()
        mock_credential.get_token.side_effect = Exception("Not logged in")

        with patch(
            "agent_app.auth.azure_identity_provider._AZURE_IDENTITY_AVAILABLE", True
        ):
            provider = AzureIdentityAuthProvider(scopes=["s1"])
            provider._credential = mock_credential
            headers = provider.get_headers()

        assert headers == {}

    def test_validate_passes_with_scopes(self) -> None:
        with patch(
            "agent_app.auth.azure_identity_provider._AZURE_IDENTITY_AVAILABLE", True
        ):
            provider = AzureIdentityAuthProvider(scopes=["s1"])
        assert provider.validate() == []

    def test_validate_reports_missing_package(self) -> None:
        with patch(
            "agent_app.auth.azure_identity_provider._AZURE_IDENTITY_AVAILABLE", False
        ):
            provider = AzureIdentityAuthProvider(scopes=["s1"])
            issues = provider.validate()
        assert any("azure-identity" in i for i in issues)

    def test_validate_reports_missing_scopes(self) -> None:
        provider = AzureIdentityAuthProvider(scopes=[])
        issues = provider.validate()
        assert any("scopes" in i for i in issues)


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

    def test_oauth_type(self) -> None:
        provider = build_auth_provider(
            {"type": "oauth", "tenant_id": "t1", "client_id": "c1"}
        )
        assert isinstance(provider, OAuthAuthProvider)

    def test_oauth_with_client_secret(self) -> None:
        with patch.dict(os.environ, {"MY_SECRET": "s"}):
            provider = build_auth_provider(
                {
                    "type": "oauth",
                    "tenant_id": "t1",
                    "client_id": "c1",
                    "scopes": ["s1"],
                    "client_secret_env_var": "MY_SECRET",
                }
            )
        assert isinstance(provider, OAuthAuthProvider)

    def test_azure_identity_type(self) -> None:
        provider = build_auth_provider(
            {"type": "azure_identity", "scopes": ["https://x/.default"]}
        )
        assert isinstance(provider, AzureIdentityAuthProvider)

    def test_unknown_type_falls_back_to_no_auth(self) -> None:
        provider = build_auth_provider({"type": "magic_auth"})
        assert isinstance(provider, NoAuthProvider)


class TestValidateCredentials:
    """ServerRegistry.validate_credentials() checks all servers."""

    def test_no_issues_when_all_valid(self) -> None:
        from agent_app.registry.server_registry import ServerRegistry

        registry = ServerRegistry(
            [
                {"label": "anon", "transport": "http", "url": "http://localhost",
                 "auth": {"type": "none"}},
            ]
        )
        assert registry.validate_credentials() == {}

    def test_reports_missing_api_key(self) -> None:
        from agent_app.registry.server_registry import ServerRegistry

        with patch.dict(os.environ, {}, clear=True):
            registry = ServerRegistry(
                [
                    {"label": "bad_key", "transport": "http", "url": "http://localhost",
                     "auth": {"type": "api_key", "header": "x-api-key",
                              "env_var": "MISSING_VAR"}},
                ]
            )
        issues = registry.validate_credentials()
        assert "bad_key" in issues
        assert len(issues["bad_key"]) >= 1

    def test_reports_missing_pat(self) -> None:
        from agent_app.registry.server_registry import ServerRegistry

        with patch.dict(os.environ, {}, clear=True):
            registry = ServerRegistry(
                [
                    {"label": "bad_pat", "transport": "stdio", "command": "node",
                     "auth": {"type": "pat", "env_var": "MISSING_PAT"}},
                ]
            )
        issues = registry.validate_credentials()
        assert "bad_pat" in issues

    def test_mixed_valid_and_invalid(self) -> None:
        from agent_app.registry.server_registry import ServerRegistry

        with patch.dict(os.environ, {"GOOD_KEY": "val"}, clear=True):
            registry = ServerRegistry(
                [
                    {"label": "good", "transport": "http", "url": "http://localhost",
                     "auth": {"type": "api_key", "header": "x-api-key",
                              "env_var": "GOOD_KEY"}},
                    {"label": "bad", "transport": "http", "url": "http://localhost",
                     "auth": {"type": "pat", "env_var": "MISSING"}},
                ]
            )
            issues = registry.validate_credentials()
        assert "good" not in issues
        assert "bad" in issues
