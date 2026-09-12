# Issue #440: Fix mock API ID generation collisions after deletions

## Description
Issue and constraint IDs were generated as `{PREFIX}-{count}` where count was `len(items) + 1`. After deletions, new items could get IDs that already exist.

## Status: COMPLETED

## Priority: HIGH

## Changes Made
1. Issue ID generation now computes max existing ID and increments from there
2. Constraint ID generation now computes max existing ID and increments from there

## Related Issues
- None
