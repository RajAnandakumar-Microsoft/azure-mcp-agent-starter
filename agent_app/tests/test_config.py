"""
Tests for configuration management.

Validates that config loading, parsing, and validation work correctly.
"""

import os
from unittest.mock import patch

import pytest

from agent_app.config import AppConfig, AzureConfig, load_config


class TestAzureConfig:
    """Tests for AzureConfig validation."""

    def test_validate_success(self) -> None:
        """Test that validation passes with valid configuration."""
        config = AzureConfig(
            project_endpoint="https://example.services.ai.azure.com/api/projects/test",
            agent_id="test-agent:1",
            subscription_id="test-sub-id",
            resource_group="test-rg",
            project_name="test-project",
        )
        # Should not raise
        config.validate()

    def test_validate_missing_endpoint(self) -> None:
        """Test that validation fails when project_endpoint is missing."""
        config = AzureConfig(
            project_endpoint="",
            agent_id="test-agent:1",
            subscription_id="test-sub-id",
            resource_group="test-rg",
            project_name="test-project",
        )
        with pytest.raises(SystemExit):
            config.validate()

    def test_validate_missing_agent_id(self) -> None:
        """Test that validation fails when agent_id is missing."""
        config = AzureConfig(
            project_endpoint="https://example.services.ai.azure.com/api/projects/test",
            agent_id="",
            subscription_id="test-sub-id",
            resource_group="test-rg",
            project_name="test-project",
        )
        with pytest.raises(SystemExit):
            config.validate()


class TestLoadConfig:
    """Tests for load_config function."""

    @patch.dict(
        os.environ,
        {
            "AZURE_EXISTING_AIPROJECT_ENDPOINT": "https://test.services.ai.azure.com/api/projects/test",
            "AZURE_EXISTING_AGENT_ID": "test-agent:1",
            "AZURE_SUBSCRIPTION_ID": "test-sub-123",
            "AZURE_EXISTING_AIPROJECT_RESOURCE_ID": "/subscriptions/test-sub/resourceGroups/test-rg/providers/Microsoft.CognitiveServices/accounts/test-account/projects/test-project",
            "AGENT_MAX_TOKENS": "500",
            "AGENT_TEMPERATURE": "0.5",
        },
        clear=True,
    )
    def test_load_config_from_env(self) -> None:
        """Test that config loads correctly from environment variables."""
        config = load_config()

        assert isinstance(config, AppConfig)
        assert config.azure.project_endpoint == "https://test.services.ai.azure.com/api/projects/test"
        assert config.azure.agent_id == "test-agent:1"
        assert config.azure.subscription_id == "test-sub-123"
        assert config.azure.resource_group == "test-rg"
        assert config.azure.project_name == "test-project"
        assert config.agent.max_tokens == 500
        assert config.agent.temperature == 0.5

    @patch.dict(
        os.environ,
        {
            "AZURE_EXISTING_AIPROJECT_ENDPOINT": "https://test.services.ai.azure.com/api/projects/test",
            "AZURE_EXISTING_AGENT_ID": "test-agent:1",
        },
        clear=True,
    )
    def test_load_config_defaults(self) -> None:
        """Test that config uses defaults when optional values not provided."""
        config = load_config()

        # Note: subscription_id, resource_group, project_name are parsed from endpoint
        assert config.agent.max_tokens == 1000  # default
        assert config.agent.temperature == 0.7  # default

    @patch.dict(os.environ, {}, clear=True)
    def test_load_config_missing_required(self) -> None:
        """Test that config loading succeeds even with missing values (uses defaults)."""
        config = load_config()
        # Should load with defaults, validation happens at runtime
        assert config is not None


class TestMainImport:
    """Tests for main module import."""

    def test_main_imports_successfully(self) -> None:
        """Test that main.py can be imported without errors."""
        # This ensures no syntax errors or import issues
        import agent_app.main

        assert hasattr(agent_app.main, "main")
        assert hasattr(agent_app.main, "run_agent_with_tools")
        assert hasattr(agent_app.main, "create_agent_client")
