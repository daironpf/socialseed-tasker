# Issue #63: Improve README Quick Start with working curl examples

## Description

The README.md contains extensive API documentation but the Quick Start section lacks a complete end-to-end example that a user can copy-paste and see immediate results. The existing examples reference placeholder UUIDs that don't exist.

## Problem Found

The README Quick Start jumps directly into curl commands with `<component-uuid>` placeholders. A new user following the docs must:
1. Start Docker Compose
2. Create a component first to get an ID
3. Then use that ID in subsequent commands

There is no "copy-paste and it works" flow. The README also doesn't mention that the board runs on port 8080 or that Neo4j Browser is on 7474.

## Impact

- Users give up when examples don't work out of the box
- Documentation feels incomplete despite being detailed
- First impression of the product suffers

## Suggested Fix

- Add a "5-minute quickstart" section with sequential curl commands that create a component, issue, and dependency in one flow
- Include the actual service URLs table (API, Board, Neo4j, Docs)
- Add a section showing how to verify everything is working: `curl http://localhost:8000/health`
- Mention that data persists in Neo4j volume between restarts

## Priority

MEDIUM

## Labels

docs, ux, onboarding
