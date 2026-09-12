# Issue #443: Fix updated_at never set on any update

## Description
PATCH endpoints for issues never updated the `updated_at` timestamp. After edits, `updated_at` always showed the creation time.

## Status: COMPLETED

## Priority: HIGH

## Changes Made
1. Issue PATCH handler now sets `updated_at` to current timestamp on every update

## Related Issues
- None
