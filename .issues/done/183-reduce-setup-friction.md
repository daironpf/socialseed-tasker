# Issue #183: Reduce Setup Friction - Auto-configure Neo4j Credentials

## Description

The setup friction score is 7/10. Users must manually configure Neo4j credentials before running the application, which adds friction to the initial setup experience.

## Problem

Currently, users must:
1. Run `tasker init .`
2. Manually copy and edit `.env` files
3. Configure Neo4j credentials manually

This adds unnecessary steps for new users.

## Expected Behavior

The application should work out-of-the-box with sensible defaults:
- Use environment variables with clear documentation
- Provide sensible defaults for Neo4j connection
- Show helpful error messages if configuration is missing

## Proposed Solutions

### Option 1: Environment Variable Defaults
Configure docker-compose.yml to use environment variables with clear defaults:
```yaml
services:
  tasker-api:
    environment:
      - TASKER_NEO4J_URI=${TASKER_NEO4J_URI:-bolt://tasker-db:7687}
      - TASKER_NEO4J_PASSWORD=${TASKER_NEO4J_PASSWORD:-neoSocial}
```

### Option 2: CLI Setup Wizard
Add an interactive setup command:
```bash
tasker setup  # Interactive wizard
```

### Option 3: Default Credentials in Scaffold
Include default credentials in scaffolded docker-compose.yml that "just work" for local development.

## Status: COMPLETED

## Priority: MEDIUM

## Component
CLI

## Suggested Fix

Implement Option 3 (Default Credentials in Scaffold) for quickest win:
1. Update docker-compose.yml template to include default credentials
2. Document in scaffolded README that credentials can be customized
3. Add comment explaining how to override for production

This would reduce setup_friction from 7 to 9.

## Impact

- Reduces time to first value for new users
- Makes local development easier
- No security impact since these are development defaults only