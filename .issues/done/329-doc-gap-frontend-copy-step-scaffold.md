# Issue #329: Frontend copy step not documented in scaffold README

## Description
The `tasker install` command places a placeholder frontend in the scaffolded project. The full frontend must be copied from the actual build output, but the generated `README.md` inside the scaffolded `.agent/tasker/` directory does not document this step.

## Expected Behavior
The scaffold README should document:
1. That the frontend is a placeholder
2. How to build the full frontend
3. How to copy the built frontend into the project

## Actual Behavior
README only shows `docker compose up -d` which uses the placeholder frontend with limited functionality.

## Steps to Reproduce
1. Run `tasker install .`
2. Look at `.agent/tasker/README.md`
3. Notice no mention of frontend copy step

## Status: PENDING

## Priority: LOW

## Component
DOCS — `src/socialseed_tasker/assets/templates/README.md` (scaffold template)

## Suggested Fix
Add a section to the scaffold README template explaining the frontend copy step, referencing the full build location.
