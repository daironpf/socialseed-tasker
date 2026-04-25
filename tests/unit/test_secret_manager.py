"""Tests for secret manager service."""

import os
import pytest
from unittest.mock import patch, MagicMock
from socialseed_tasker.core.services.secret_manager import (
    SecretManager,
    GitHubCredentials,
    get_secret_manager,
    get_github_token,
    validate_credentials,
    get_webhook_secret,
)


class TestGitHubCredentials:
    """Test cases for GitHubCredentials dataclass."""

    def test_masked_token_full_token(self):
        """Should mask token showing last 4 characters."""
        cred = GitHubCredentials(repo="test", token="ghp_abcdefghijklmnopqrstuvwxyz123456789012345678")
        result = cred.masked_token()
        assert "****" in result

    def test_masked_token_short_token(self):
        """Should return **** for tokens <= 8 chars."""
        cred = GitHubCredentials(repo="test", token="ghp_abcd")
        result = cred.masked_token()
        assert result == "****"

    def test_default_flag(self):
        """Should correctly identify default credentials."""
        default_cred = GitHubCredentials(repo="", token="token", is_default=True)
        repo_cred = GitHubCredentials(repo="my-repo", token="token", is_default=False)

        assert default_cred.is_default is True
        assert repo_cred.is_default is False


class TestSecretManager:
    """Test cases for SecretManager class."""

    def test_no_credentials_loaded_initially(self):
        """Should start with no credentials when env vars not set."""
        with patch.dict(os.environ, {}, clear=True):
            manager = SecretManager()
            assert manager.validate_credentials() is False

    def test_loads_default_token(self):
        """Should load GITHUB_TOKEN from environment."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_abcdefghijklmnopqrstuvwxyz1234567890123"}, clear=True):
            manager = SecretManager()
            assert manager.get_github_token() == "ghp_abcdefghijklmnopqrstuvwxyz1234567890123"
            assert manager.validate_credentials() is True

    def test_loads_repo_specific_token(self):
        """Should load GITHUB_REPO_{name}_TOKEN from environment."""
        env = {
            "GITHUB_TOKEN": "ghp_defaulttoken1234567890123456789012345678",
            "GITHUB_REPO_MYAPP_TOKEN": "ghp_myapptoken1234567890123456789012345678",
        }
        with patch.dict(os.environ, env, clear=True):
            manager = SecretManager()
            assert manager.get_github_token("MYAPP") == "ghp_myapptoken1234567890123456789012345678"
            repos = manager.list_configured_repos()
            assert "MYAPP" in repos

    def test_returns_default_for_unconfigured_repo(self):
        """Should return default token when specific repo not configured."""
        env = {"GITHUB_TOKEN": "ghp_defaulttoken1234567890123456789012345678"}
        with patch.dict(os.environ, env, clear=True):
            manager = SecretManager()
            result = manager.get_github_token("unconfigured-repo")
            assert result == "ghp_defaulttoken1234567890123456789012345678"

    def test_returns_none_when_no_token(self):
        """Should return None when no credentials configured."""
        with patch.dict(os.environ, {}, clear=True):
            manager = SecretManager()
            assert manager.get_github_token() is None

    def test_invalid_token_format_rejected(self):
        """Should reject tokens with invalid format."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "not-a-valid-token"}, clear=True):
            manager = SecretManager()
            assert manager.validate_credentials() is False

    def test_rotate_token_valid_format(self):
        """Should update token when valid format provided."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_oldtoken1234567890123456789012345678"}, clear=True):
            manager = SecretManager()
            new_token = "ghp_newtoken1234567890123456789012345678"
            manager.rotate_token("", new_token)
            assert manager.get_github_token() == new_token

    def test_rotate_token_invalid_format_raises(self):
        """Should raise ValueError when invalid format provided."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_oldtoken1234567890123456789012345678"}, clear=True):
            manager = SecretManager()
            with pytest.raises(ValueError, match="Invalid token format"):
                manager.rotate_token("", "short")

    def test_list_configured_repos(self):
        """Should list all configured repos including default."""
        env = {
            "GITHUB_TOKEN": "ghp_defaulttoken1234567890123456789012345678",
            "GITHUB_REPO_APP1_TOKEN": "ghp_app1token1234567890123456789012345678",
            "GITHUB_REPO_APP2_TOKEN": "ghp_app2token1234567890123456789012345678",
        }
        with patch.dict(os.environ, env, clear=True):
            manager = SecretManager()
            repos = manager.list_configured_repos()
            assert "" in repos
            assert "APP1" in repos
            assert "APP2" in repos

    def test_get_webhook_secret(self):
        """Should return webhook secret from environment."""
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": "my-secret"}, clear=True):
            manager = SecretManager()
            assert manager.get_webhook_secret() == "my-secret"

    def test_has_webhook_secret(self):
        """Should correctly report webhook secret presence."""
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": "secret"}, clear=True):
            manager = SecretManager()
            assert manager.has_webhook_secret() is True

        with patch.dict(os.environ, {}, clear=True):
            manager = SecretManager()
            assert manager.has_webhook_secret() is False

    def test_clear_credentials(self):
        """Should clear all credentials from memory."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_token1234567890123456789012345678"}, clear=True):
            manager = SecretManager()
            manager.clear_credentials()
            assert manager.get_github_token() is None
            assert manager.validate_credentials() is False

    def test_get_credentials_info(self):
        """Should return masked credential information."""
        env = {"GITHUB_TOKEN": "ghp_token1234567890123456789012345678901"}
        with patch.dict(os.environ, env, clear=True):
            manager = SecretManager()
            info = manager.get_credentials_info()
            assert info == {"": "****8901"}

    def test_validate_token_valid_formats(self):
        """Should validate various valid token formats."""
        manager = SecretManager()
        valid_tokens = [
            "ghp_abcdefghijklmnopqrstuvwxyz12345678901234",
            "gho_abcdefghijklmnopqrstuvwxyz12345678901234",
            "ghs_abcdefghijklmnopqrstuvwxyz12345678901234",
            "ghu_abcdefghijklmnopqrstuvwxyz12345678901234",
            "ghsa_abcdefghijklmnopqrstuvwxyz1234567890",
        ]
        for token in valid_tokens:
            assert manager.validate_token(token) is True

    def test_validate_token_invalid_formats(self):
        """Should reject invalid token formats."""
        manager = SecretManager()
        invalid_tokens = [
            "",
            "short",
            "not_a_token",
            "invalid_prefix_abc123",
            "ghp_",  # too short
        ]
        for token in invalid_tokens:
            assert manager.validate_token(token) is False


class TestStandaloneFunctions:
    """Test cases for standalone helper functions."""

    def test_get_github_token_uses_singleton(self):
        """Should use the singleton secret manager."""
        with patch("socialseed_tasker.core.services.secret_manager.get_secret_manager") as mock_get:
            mock_manager = MagicMock()
            mock_manager.get_github_token.return_value = "ghp_token123456789012345678901"
            mock_get.return_value = mock_manager
            result = get_github_token()
            assert result == "ghp_token123456789012345678901"

    def test_validate_credentials_uses_singleton(self):
        """Should use singleton for validation."""
        with patch("socialseed_tasker.core.services.secret_manager.get_secret_manager") as mock_get:
            mock_manager = MagicMock()
            mock_manager.validate_credentials.return_value = True
            mock_get.return_value = mock_manager
            assert validate_credentials() is True

    def test_get_webhook_secret_uses_singleton(self):
        """Should use singleton for webhook secret."""
        with patch("socialseed_tasker.core.services.secret_manager.get_secret_manager") as mock_get:
            mock_manager = MagicMock()
            mock_manager.get_webhook_secret.return_value = "webhook-secret"
            mock_get.return_value = mock_manager
            assert get_webhook_secret() == "webhook-secret"


class TestGetSecretManagerSingleton:
    """Test cases for get_secret_manager singleton."""

    @patch("socialseed_tasker.core.services.secret_manager._secret_manager_instance", None)
    def test_returns_same_instance(self):
        """Should return the same instance on multiple calls."""
        env = {"GITHUB_TOKEN": "ghp_token123456789012345678901234"}
        with patch.dict(os.environ, env, clear=True):
            manager1 = get_secret_manager()
            manager2 = get_secret_manager()
            assert manager1 is manager2
