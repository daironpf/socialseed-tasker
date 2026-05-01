# Workflow: Convert Findings to Issues

## Trigger Command
`convert findings` or `findings to issues`

## Description
Converts FINDings in report.md to issues in .issues/to-do/. This workflow is executed after completing a project evaluation (test the project).

---

## ⚠️ RULES

1. Only execute AFTER report.md is complete
2. DO NOT create issues for problems already resolved
3. Maintain index correlation with .issues/done/

---

## Phase 1: Read report.md

### Process
1. Read the file: `real-test/report.md`
2. Find all sections with `### FIND-###:` pattern
3. Extract:
   - ID (FIND-001, FIND-002, etc.)
   - Type (BUG, DOC_GAP, etc.)
   - Severity
   - Title
   - Description

---

## Phase 2: Create Issues

### For Each FINDING

Create a new issue file in `.issues/to-do/` with:

```markdown
# Issue #XXX: [Title from Finding]

## Description
[Copy description from finding]

## Expected Behavior
[If mentioned in finding]

## Actual Behavior
[If mentioned in finding]

## Steps to Reproduce
1. [Steps from finding or infer]

## Status: PENDING

## Priority: [SEVERITY]

## Component
[Component from finding]

## Suggested Fix
[Suggested fix from finding]

## Impact
[Impact from finding]

## Related Issues
- Related issue numbers from previous runs
```

### Index Correlation
- Find highest issue number in `.issues/done/`
- New issues continue from that number (e.g., if highest is 171, next is 172)

---

## Phase 3: Update report.md

### Process
1. Add to report.md:
```
### Issues Created from Findings

| Issue | Title |
|-------|-------|
| #172 | [title FIND-001] |
| #173 | [title FIND-002] |
```

---

## Phase 4: Notify

### Output
Report to user:
```
Issues created:
- .issues/to-do/172-[slug].md
- .issues/to-do/173-[slug].md
```

---

## Example

### Input (report.md)
```markdown
### FIND-001: API returns wrong version

| Severity | HIGH |
|----------|------|
| Title | Version mismatch |

API returns 0.7.0 instead of 0.9.0
```

### Output (.issues/to-do/172-version-mismatch.md)
```markdown
# Issue #172: API returns wrong version

## Description
API returns 0.7.0 instead of 0.9.0

## Expected Behavior
Version should match source code

## Status: PENDING

## Priority: HIGH
...
```

---

## Checklist

- [ ] Read real-test/report.md
- [ ] Extract all FIND-### sections
- [ ] Create issue for each FINDING (not RESOLVED)
- [ ] Maintain index correlation
- [ ] Update report.md with created issues
- [ ] Notify user of created issues