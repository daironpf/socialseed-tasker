# Issue #170: Frontend Board Not Included in Docker Compose

## Description
The tasker-board (Vue.js frontend/Kanban board UI) was not included in the scaffolded docker-compose.yml. When attempting to include it, the build fails because the frontend source code is not in the scaffolded directory.

## Expected Behavior
Scaffolded docker-compose.yml should either:
1. Include working frontend service, OR
2. Document frontend as optional with setup instructions

## Actual Behavior
When including tasker-board in docker-compose.yml:
```
Image tasker-tasker-board Building
resolve: GetFileAttributesEx .../frontend: El sistema no puede encontrar el archivo especificado.
```

## Steps to Reproduce
1. Run `tasker init .`
2. Edit generated docker-compose.yml to uncomment tasker-board
3. Run `docker compose up -d`
4. Observe build failure

## Status: PENDING

## Priority: MEDIUM

## Component
Infrastructure (tasker init, scaffolding, frontend)

## Suggested Fix
Option A: Include frontend in scaffolded structure
- Add frontend/ directory to templates
- Update Dockerfile to build both API and frontend

Option B: Remove frontend service entirely
- Document that frontend is optional
- Provide link to separate repository for UI

Option C: Use pre-built image
- Provide tasker-board in docker-compose that uses pre-built image

## Impact
Users cannot access visual Kanban board UI. Only API available for interaction.

## Related Issues
- Issue #167: tasker init incomplete docker-compose (related)
- Issue #168: Missing documentation in scaffold (related)
- Real-Test Evaluation Profile: DevOps, Junior Dev

(End of file - total 52 lines)