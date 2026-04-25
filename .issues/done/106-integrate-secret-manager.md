# Issue #106: Integrate SecretManager with GitHub Services

## Description

The SecretManager service was implemented (Issue #97) but is not being used by the GitHub API adapter and other services that need credential management. The credentials are still being read directly from environment variables instead of using the centralized service.

## Requirements

- Replace direct `os.environ.get("GITHUB_TOKEN")` calls with SecretManager
- Use SecretManager for webhook secret retrieval
- Use SecretManager in GitHub API adapter for token management
- Implement token rotation using the SecretManager API
- Add credential validation at startup using SecretManager.validate_credentials()

## Technical Details

### Current Implementation Issues
Throughout the codebase, credentials are read directly:
```python
# In various files
webhook_secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
github_token = os.environ.get("GITHUB_TOKEN", "")
```

### Service Implementation (exists but not used)
Location: `src/socialseed_tasker/core/services/secret_manager.py`

```python
class SecretManager:
    def get_github_token(self, repo: str = "") -> str | None
    def validate_credentials(self) -> bool
    def rotate_token(self, repo: str, new_token: str) -> None
    def get_webhook_secret(self) -> str
    def has_webhook_secret(self) -> bool
    def get_credentials_info(self) -> dict  # Returns masked info
```

### Integration Points
1. **Webhook endpoint** - Use `get_webhook_secret()` instead of `os.environ`
2. **GitHub API adapter** - Use `get_github_token(repo)` for authenticated requests
3. **Container startup** - Call `validate_credentials()` to ensure credentials exist
4. **Health endpoint** - Include credential status (without exposing secrets)

### Container Integration (already added but not used)
```python
def get_secret_manager(self) -> SecretManager:
    from socialseed_tasker.core.services.secret_manager import SecretManager
    return SecretManager()
```

### Example Usage After Fix
```python
from socialseed_tasker.core.services.secret_manager import get_secret_manager

def handle_webhook(request):
    sm = get_secret_manager()
    secret = sm.get_webhook_secret()
    # Use secret for validation
```

## Business Value

Centralized credential management provides:
- Consistent credential handling across all services
- Token rotation without restarting the application
- Better error handling for missing credentials
- Security audit trail

## Status: COMPLETED