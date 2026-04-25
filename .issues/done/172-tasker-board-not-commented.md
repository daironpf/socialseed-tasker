# Issue #172: tasker-board Should NOT Be Commented in Scaffolded Template

## Description
The scaffolded docker-compose.yml template has tasker-board (frontend/Kanban board) commented out, but users expect it to work like the main project where it's active.

## Expected Behavior
tasker-board should be active and working in scaffolded projects, matching main project's docker-compose.yml.

## Actual Behavior
Template has:
```yaml
# tasker-board:
#   container_name: tasker-board
#   image: placeholder
```

Main project has:
```yaml
tasker-board:
  container_name: tasker-board
  build:
    context: .
    dockerfile: frontend/Dockerfile
```

## Steps to Reproduce
1. Run `tasker init .`
2. Check generated `tasker/docker-compose.yml`
3. See tasker-board is commented

## Status: COMPLETED

## Resolution
Updated docker-compose template to include tasker-board as ACTIVE service:
- Uses pre-built image: ghcr.io/daironpf/socialseed-tasker-board:latest
- tasker-board is now uncomented and works with docker compose up -d

## Priority: HIGH

## Component
Infrastructure (tasker init, scaffolding)

## Suggested Fix
- Uncomment tasker-board in template
- Use pre-built image: ghcr.io/daironpf/socialseed-tasker-board:latest
- Or copy build context from main project

## Impact
Users expect full functionality like main project.

## Related Issues
- Issue #171: tasker-board format (related)
- Issue #170: Frontend board

(End file - 45 lines)