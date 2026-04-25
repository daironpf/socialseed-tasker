# Issue #69: Add API key authentication for production use

## Description

The API has no authentication. Anyone with network access can create, modify, and delete issues and components. This is acceptable for local development but not for any production or shared deployment.

## Problem Found

The README states "Currently no authentication required." During testing, any curl command could modify data without credentials. The `ALLOWED_ORIGINS` env var is mentioned but no auth mechanism exists.

## Impact

- Cannot deploy Tasker in shared environments safely
- AI agents cannot securely connect to remote instances
- No audit trail of who made changes
- Risk of accidental or malicious data modification

## Suggested Fix

- Add API key authentication via `X-API-Key` header
- Store API keys hashed in Neo4j with creation date, permissions, and expiry
- Add `POST /api/v1/admin/api-keys` to generate new keys
- Support read-only and read-write key scopes
- Add `TASKER_API_KEY` env var for single-key simple mode
- Document authentication in README and API docs

## Priority

HIGH

## Labels

security, api, production
