# Issue #219 - Document Neo4j Password Requirement

## Description

Neo4j container fails to start if password is "neo4j" (the default). Error message in logs: "Invalid value for password. It cannot be 'neo4j', which is the default."

## Problem

```bash
# Fails
docker run -e NEO4J_AUTH=neo4j/neo4j neo4j:5.26.15-community
# Error: Invalid value for password. It cannot be 'neo4j', which is the default.

# Works
docker run -e NEO4J_AUTH=neo4j/neoSocial neo4j:5.26.15-community
```

## Root Cause

Neo4j 5.x doesn't allow setting password to "neo4j" (the default username) for security reasons.

## Expected Behavior

README.md or docker-compose.yml should document that:
1. Default password cannot be "neo4j"
2. Use a different password (e.g., "neoSocial")

## Implementation Steps

### Step 1: Update docker-compose.yml

Add comment explaining password requirement.

### Step 2: Update README.md

Add "Troubleshooting" section with Neo4j password instructions.

## Affected Files

- `docker-compose.yml`
- `README.md`

## Priority

MEDIUM

## Status: COMPLETED