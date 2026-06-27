# Issue #223: Pre-emptive Impact Analysis during Issue Creation

## Description
Analyze the potential risk of an issue at the moment it is created by linking it to a component and its code graph.

## Acceptance Criteria
- [x] Automatic impact calculation on `issue create`.
- [x] Risk score (LOW/MEDIUM/HIGH) based on call graph depth of the component.
- [x] Warning if an issue affects "Hot Files" (frequently modified or highly coupled).

## Status: DONE

## Resolution (2026-05-04)
- [x] Add _compute_preemptive_impact function
- [x] Risk level based on code graph (callers count, files count)
- [x] HOT FILES warning on issue creation
- [x] Warnings returned in create_issue_action

### Files Changed
- `actions.py`: Added _compute_preemptive_impact function

### Usage
```bash
# Automatic - warnings shown on issue create
tasker issue create "Fix bug" -c component -p HIGH

# Warnings example output:
# - HIGH RISK: Component has 25 files, risk: HIGH
# - HOT FILES: May affect frequently modified: file1.py, file2.py
```

### Risk Levels
| Level | Callers | Files | Action |
|-------|--------|-------|--------|
| LOW | 0 | <10 | No warning |
| MEDIUM | 1-2 | 10-20 | Info |
| HIGH | 3-5 | 20-50 | Warning |
| CRITICAL | >5 | >50 | Warning |
