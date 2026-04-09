"""Secret manager for secure GitHub credential handling.

Manages GitHub Personal Access Tokens (PAT) via environment injection.
Credentials are loaded from environment variables, validated on access,
and masked in logs to prevent exposure.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class GitHubCredentials:
    """Represents GitHub credentials for a repository."""

    repo: str
    token: str
    is_default: bool = False

    def masked_token(self) -> str:
        """Return masked token showing only last 4 characters."""
        if len(self.token) <= 8:
            return "****"
        return f"****{self.token[-4:]}"


class SecretManager:
    """Manages secure GitHub credentials from environment variables."""

    TOKEN_PATTERN = re.compile(r"^gh(p|o|s|u|sa|sr)_[A-Za-z0-9_]{20,251}$")

    def __init__(self) -> None:
        self._credentials: dict[str, GitHubCredentials] = {}
        self._default_token: str | None = None
        self._load_credentials()

    def _load_credentials(self) -> None:
        """Load credentials from environment variables."""
        default_token = os.environ.get("GITHUB_TOKEN", "")
        if default_token:
            if self._validate_token_format(default_token):
                self._default_token = default_token
                self._credentials[""] = GitHubCredentials(
                    repo="",
                    token=default_token,
                    is_default=True,
                )
                logger.info("Loaded default GitHub token")
            else:
                logger.warning("GITHUB_TOKEN has invalid format")

        for key, value in os.environ.items():
            if key.startswith("GITHUB_REPO_") and key.endswith("_TOKEN"):
                repo_name = key[12:-6]
                if self._validate_token_format(value):
                    self._credentials[repo_name] = GitHubCredentials(
                        repo=repo_name,
                        token=value,
                        is_default=False,
                    )
                    logger.info(f"Loaded GitHub token for repo: {repo_name}")

    def _validate_token_format(self, token: str) -> bool:
        """Validate token format (ghp_, gho_, ghsa_, ghsr_, ghusr_)."""
        if not token or len(token) < 20:
            return False
        return bool(self.TOKEN_PATTERN.match(token))

    def get_github_token(self, repo: str = "") -> str | None:
        """Get GitHub token for a repository.

        Args:
            repo: Repository name (empty string for default token)

        Returns:
            Token string or None if not configured
        """
        if repo and repo in self._credentials:
            creds = self._credentials[repo]
            logger.debug(f"Using token for repo {repo}: {creds.masked_token()}")
            return creds.token

        if self._default_token:
            logger.debug(f"Using default token: {self._credentials[''].masked_token()}")
            return self._default_token

        logger.warning(f"No GitHub token configured for repo: {repo}")
        return None

    def validate_credentials(self) -> bool:
        """Validate that at least one credential is configured and valid.

        Returns:
            True if valid credentials exist
        """
        if not self._default_token and not self._credentials:
            return False

        for cred in self._credentials.values():
            if self._validate_token_format(cred.token):
                return True

        return False

    def rotate_token(self, repo: str, new_token: str) -> None:
        """Update token for a repository.

        Args:
            repo: Repository name (empty string for default)
            new_token: New token to store

        Raises:
            ValueError: If token format is invalid
        """
        if not self._validate_token_format(new_token):
            raise ValueError("Invalid token format. Expected GitHub PAT format (ghp_*, gho_*, etc.)")

        is_default = repo == ""
        self._credentials[repo] = GitHubCredentials(
            repo=repo,
            token=new_token,
            is_default=is_default,
        )

        if is_default:
            self._default_token = new_token

        logger.info(f"Rotated token for repo '{repo}': {self._credentials[repo].masked_token()}")

    def list_configured_repos(self) -> list[str]:
        """List all configured repository names.

        Returns:
            List of repository names (empty string represents default)
        """
        return list(self._credentials.keys())

    def get_webhook_secret(self) -> str:
        """Get GitHub webhook secret.

        Returns:
            Webhook secret or empty string if not configured
        """
        return os.environ.get("GITHUB_WEBHOOK_SECRET", "")

    def has_webhook_secret(self) -> bool:
        """Check if webhook secret is configured.

        Returns:
            True if GITHUB_WEBHOOK_SECRET is set
        """
        return bool(self.get_webhook_secret())

    def clear_credentials(self) -> None:
        """Clear all stored credentials from memory."""
        self._credentials.clear()
        self._default_token = None
        logger.info("Cleared all GitHub credentials from memory")

    def get_credentials_info(self) -> dict[str, Any]:
        """Get masked information about configured credentials.

        Returns:
            Dict with repo names and masked tokens (for debugging)
        """
        return {repo: cred.masked_token() for repo, cred in self._credentials.items()}

    def validate_token(self, token: str) -> bool:
        """Validate a single token format.

        Args:
            token: Token to validate

        Returns:
            True if token format is valid
        """
        return self._validate_token_format(token)


_secret_manager_instance: SecretManager | None = None


def get_secret_manager() -> SecretManager:
    """Get the global secret manager instance."""
    global _secret_manager_instance
    if _secret_manager_instance is None:
        _secret_manager_instance = SecretManager()
    return _secret_manager_instance


def get_github_token(repo: str = "") -> str | None:
    """Standalone function to get GitHub token."""
    return get_secret_manager().get_github_token(repo)


def validate_credentials() -> bool:
    """Standalone function to validate credentials."""
    return get_secret_manager().validate_credentials()


def get_webhook_secret() -> str:
    """Standalone function to get webhook secret."""
    return get_secret_manager().get_webhook_secret()
