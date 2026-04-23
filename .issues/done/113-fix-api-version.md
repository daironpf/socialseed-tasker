# Issue #113: Fix API Version Mismatch in Health Endpoint

## Description

The health endpoint (`/health`) returns version "0.5.0" or "0.6.0" but the project version is 0.8.0. This causes version confusion for API clients.

## Current Behavior
```json
GET /health
{
  "status": "healthy",
  "version": "0.5.0"  // Should be 0.8.0
}
```

## Expected Behavior
```json
GET /health
{
  "status": "healthy",
  "version": "0.8.0"
}
```

## Requirements

- Fix health endpoint to return correct version
- Use dynamic version from package/__init__.py or pyproject.toml

## Status: COMPLETED