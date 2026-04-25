# Issue #103: Fix Webhook Test Endpoint Method (405 Error)

## Description

The webhook test endpoint at `/api/v1/webhooks/github/test` returns 405 Method Not Allowed when accessed via GET request. The endpoint needs proper GET method handling for testing webhook configuration.

## Requirements

- Fix the webhook test endpoint to accept GET requests
- Ensure the endpoint returns proper configuration status
- Add proper response schema for the test endpoint
- Add tests for the webhook test functionality

## Technical Details

### Current Behavior
```bash
GET /api/v1/webhooks/github/test
# Returns: 405 Method Not Allowed
```

### Expected Behavior
```bash
GET /api/v1/webhooks/github/test
# Returns: 200 OK
{
  "success": true/false,
  "message": "Webhook configuration valid" / "GITHUB_WEBHOOK_SECRET not configured"
}
```

### Location
The endpoint is defined in `src/socialseed_tasker/entrypoints/web_api/routes.py` around line 2029.

### Current Implementation (needs fix)
```python
@webhook_router.post(  # Should be GET or add GET method
    "/webhooks/github/test",
    response_model=APIResponse[GitHubWebhookTestResponse],
    ...
)
def test_webhook(request: Request = None):
    ...
```

### Solution
Change from POST to GET, or add GET as an additional method:
```python
@webhook_router.get(
    "/webhooks/github/test",
    ...
)
def test_webhook():
    # Return webhook configuration status
```

## Business Value

The webhook test endpoint is essential for verifying that the webhook configuration is correct before deploying to production.

## Status: COMPLETED