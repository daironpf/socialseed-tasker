# Issue #105: Integrate WebhookSignatureValidator Service with Routes

## Description

The WebhookSignatureValidator service was implemented (Issue #95) but is not being used in the actual webhook endpoint. The routes.py file has its own `_verify_github_signature` function instead of using the centralized service.

## Requirements

- Replace the inline `_verify_github_signature` function in routes.py with the WebhookSignatureValidator service
- Add the validator to the Container for dependency injection
- Use the validator's rejected log feature for security auditing
- Ensure environment variable GITHUB_WEBHOOK_SECRET is properly used

## Technical Details

### Current Implementation (in routes.py)
```python
def _verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook HMAC-SHA256 signature."""
    import hmac
    import hashlib

    if not signature or not secret:
        return True

    expected = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### Service Implementation (exists but not used)
Location: `src/socialseed_tasker/core/services/webhook_validator.py`

```python
class WebhookSignatureValidator:
    def __init__(self, secret: str | None = None) -> None:
        self._secret = secret or os.environ.get("GITHUB_WEBHOOK_SECRET", "")
        
    def validate(self, payload: bytes, signature: str) -> bool:
        # Full implementation with logging
```

### Integration Steps
1. Import WebhookSignatureValidator in routes.py
2. Create a dependency that gets the validator from the container
3. Replace `_verify_github_signature` call with validator.validate()
4. Use the rejected log for security monitoring endpoint

### Container Integration (exists but not used)
```python
def get_webhook_validator(self) -> WebhookSignatureValidator:
    from socialseed_tasker.core.services.webhook_validator import WebhookSignatureValidator
    return WebhookSignatureValidator(secret=os.environ.get("GITHUB_WEBHOOK_SECRET", ""))
```

## Business Value

Using the centralized service provides:
- Consistent signature validation across all webhook endpoints
- Security audit logging for rejected requests
- Easier maintenance and testing
- Reusable code

## Status: COMPLETED