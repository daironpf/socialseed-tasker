# Issue #222: Autonomous Architect Agent for Rule Enforcement

## Description
Implement a specialized Agent role that automatically reviews proposed changes against architectural constraints.

## Acceptance Criteria
- [x] Agent role `ARCHITECT` logic implementation.
- [x] Integration with `tasker.constraints.yml`.
- [x] Validation of `core/` imports to ensure no framework leakage.
- [x] Automatic "Veto" if constraints are violated.

## Status: DONE

## Resolution (2026-05-04)
- [x] Added `ARCHITECT` role to AgentRole enum
- [x] CLI: `tasker agent architect --issue <id> --check`
- [x] Validates against existing constraint system
- [x] Returns ARCHITECT APPROVED or VETO

### Files Changed
- `entities.py`: Added ARCHITECT role
- `commands.py`: Added agent architect command

### Usage
```bash
# Review an issue against constraints
tasker agent architect --issue <issue_id>

# Check only (don't veto)
tasker agent architect --issue <issue_id> --check
```
