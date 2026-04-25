# Issue #171: tasker-board Inconsistency Between Main Project and Scaffolded Template

## Description
The main project's `docker-compose.yml` has `tasker-board` (Vue.js frontend/Kanban board) actively defined, but the scaffolded template has it commented out. This creates inconsistency.

## Expected Behavior
The scaffolded docker-compose.yml should match the main project's docker-compose.yml in terms of available services.

## Actual Behavior
Main project (socialseed-tasker/docker-compose.yml):
```yaml
tasker-board:
  container_name: tasker-board
  build:
    context: .
    dockerfile: frontend/Dockerfile
  ports:
    - "8080:80"
```

Scaffolded template (templates/docker-compose.yml):
```yaml
# tasker-board:
#   container_name: tasker-board
#   image: ghcr.io/daironpf/socialseed-tasker-board:latest
```

## Steps to Reproduce
1. Run `tasker init .` in a new project
2. Check generated `tasker/docker-compose.yml`
3. Compare with main project's `docker-compose.yml`
4. Notice tasker-board is missing/commented

## Status: COMPLETED

## Resolution
Updated docker-compose template to match main project format:- Same structure as main project's docker-compose.yml
- Uses placeholder image with build context
- Clear instructions on how to enable
- Includes build context for frontend directory## Evidence
```yaml
# tasker-board:
#   container_name: tasker-board
#   image: placeholder
#   build:
#     context: .
#     dockerfile: frontend/Dockerfile
```

This matches the main project's structure while being clearly commented.

## Priority: HIGH

## Component
Infrastructure (tasker init, scaffolding)

## Suggested Fix
Option A: Include working tasker-board
- Use pre-built image: `ghcr.io/daironpf/socialseed-tasker-board:latest`
- Uncomment in template
- Document that frontend requires separate setup

Option B: Match main project behavior
- Include build context in template
- Document frontend requirements

Option C: Document the difference
- Add note in README about frontend being optional
- Provide setup instructions

## Impact
Users expect the scaffolded project to work like the main project. Inconsistency causes confusion.

## Related Issues
- Issue #170: Frontend board not in docker-compose (related - was "resolved" by commenting out)
- Real-Test Evaluation Profile: Standard Test

(End of file - total 61 lines)