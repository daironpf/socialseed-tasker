"""Credential management utilities for CLI."""

from __future__ import annotations

import json
from pathlib import Path

_CLI_CONFIG_FILE = Path.home() / ".tasker" / "credentials"


def load_saved_credentials() -> dict[str, str]:
    """Load saved credentials from local config file."""
    config_file = _CLI_CONFIG_FILE
    if config_file.exists():
        try:
            with open(config_file) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def save_credentials(uri: str, user: str, password: str) -> None:
    """Save credentials to local config file."""
    config_file = _CLI_CONFIG_FILE
    config_file.parent.mkdir(parents=True, exist_ok=True)
    credentials = {
        "uri": uri,
        "user": user,
        "password": password,
    }
    with open(config_file, "w") as f:
        json.dump(credentials, f)


def clear_credentials() -> None:
    """Clear saved credentials."""
    config_file = _CLI_CONFIG_FILE
    if config_file.exists():
        config_file.unlink()


def get_config_file_path() -> Path:
    """Get the credentials config file path."""
    return _CLI_CONFIG_FILE
