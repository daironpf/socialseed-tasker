# Issue #95: WebhookSignatureValidator

## Description

Implement secure endpoint for real-time bidirectional sync from GitHub. Validates incoming webhook requests to prevent spoofing attacks.

## Requirements

- Implement HMAC-SHA256 signature validation
- Support GitHub's signature format (sha256=...)
- Reject requests with invalid/missing signatures
- Add configurable secret via environment variable
- Log rejected requests for security auditing
- Support testing endpoint with manual signature

## Technical Details

### Signature Validation
```python
import hmac
import hashlib

def validate_signature(payload: bytes, secret: str, signature: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

### Configuration
- `GITHUB_WEBHOOK_SECRET` - Secret for signature validation

### Endpoint
- `POST /webhooks/github` - Validates signature before processing

## Business Value

Secures webhook endpoints against malicious requests. Only verified GitHub events are processed.

## Status: DONE