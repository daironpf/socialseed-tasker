# Issue #444: Fix new issues missing required fields

## Description
The `createIssue` endpoint did not include `blocks`, `affects`, `architectural_constraints`, `updated_at`, or `agent_working` fields, causing potential runtime errors.

## Status: COMPLETED

## Priority: HIGH

## Changes Made
1. Added `blocks: []`, `affects: []`, `architectural_constraints: []`, `updated_at`, `agent_working: False` to new issue creation

## Related Issues
- None
