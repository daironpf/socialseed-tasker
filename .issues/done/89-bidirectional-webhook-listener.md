# Issue #89: Bidirectional Webhook Listener

## Description

Implement API endpoint to receive real-time updates from GitHub (comments, label changes, status updates). This enables Tasker to stay in sync with GitHub changes.

## Requirements

- Create webhook endpoint: `POST /webhooks/github`
- Validate webhook signature using HMAC-SHA256
- Handle GitHub event types: issues, issue_comment, label, milestone
- Parse payload and update Neo4j accordingly
- Support configurable event routing (which events trigger sync)
- Add retry logic for processing failures
- Store webhook delivery logs for debugging

## Technical Details

### Webhook Events to Handle
- `issues` - Issue created, closed, reopened, edited
- `issue_comment` - Comments added/edited/deleted
- `label` - Labels added/removed
- `milestone` - Milestone created, closed, edited

### Endpoint
- `POST /webhooks/github` - Receive GitHub webhook
- `GET /webhooks/github/logs` - View delivery logs
- `POST /webhooks/github/test` - Test webhook configuration

### Security
- Validate `X-Hub-Signature-256` header
- Support webhook secret via `GITHUB_WEBHOOK_SECRET`

## Business Value

Enables real-time bidirectional sync. Changes in GitHub are reflected in Tasker without polling.

## Status: COMPLETED