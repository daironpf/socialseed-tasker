# Issue #97: SecretManager

## Description

Implement secure handling of GitHub Personal Access Tokens (PAT) via environment injection. Manages API credentials securely without hardcoding or logging.

## Requirements

- Create SecretManager service for credential management
- Load credentials from environment variables
- Validate credentials on startup
- Mask credentials in logs (never expose full token)
- Support multiple GitHub accounts (for different repositories)
- Implement token refresh mechanism (if using OAuth)
- Add rotation support (update token without restart)

## Technical Details

### SecretManager Interface
```python
class SecretManager:
    def get_github_token(self, repo: str) -> str: ...
    def validate_credentials(self) -> bool: ...
    def rotate_token(self, repo: str, new_token: str) -> None: ...
    def list_configured_repos(self) -> list[str]: ...
```

### Environment Variables
- `GITHUB_TOKEN` - Default token for all repos
- `GITHUB_REPO_{name}_TOKEN` - Token for specific repo
- `GITHUB_WEBHOOK_SECRET` - Webhook validation secret

### Security Measures
- Token never logged in full (show last 4 chars only)
- Token stored in memory, not persisted to disk
- Validate token format before storing
- Clear credentials on shutdown

## Business Value

Secure credential management is essential for GitHub integration. Prevents token exposure and enables secure multi-repo support.

## Status: DONE