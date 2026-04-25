# Issue #123: Add Webhook Secret Validation

## Description

Add proper webhook secret validation and error handling when secret is not configured.

## Current State

- Webhook test returns success=false when secret not set
- No actual validation when receiving webhooks
- Could accept any payload

## Problem

```
GET /api/v1/webhooks/github/test
{
  "data": {
    "success": false,
    "message": "GITHUB_WEBHOOK_SECRET not configured"
  }
}
```

But there's no actual validation - webhooks are accepted without checking.

## Requirements

- Validate webhook signature on incoming requests
- Return 401 for invalid signatures
- Add GITHUB_WEBHOOK_SECRET validation
- Add logging for rejected webhooks

## Implementation

```python
# In webhook handler
def handle_webhook(request: Request):
    signature = request.headers.get("X-Hub-Signature-256")
    if not validator.validate(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
```

## Status: COMPLETED