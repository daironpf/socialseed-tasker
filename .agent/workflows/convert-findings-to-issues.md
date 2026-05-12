# Workflow: Convert Findings to Issues

## Trigger Command
`convert findings` or `findings to issues`

## Description
Converts FINDings in report.md to issues in .issues/to-do/. This workflow is executed after completing a project evaluation (test the project).

---

## ⚠️ RULES

1. Only execute AFTER report.md is complete
2. DO NOT create issues for problems already resolved
3. **ALWAYS** use `.issues/done/` folder to determine the correct index (NOT the INDEX file in to-do)
4. The issue number must be the next sequential number after the highest numbered file in `.issues/done/`

---

## Phase 1: Determine Correct Issue Index

### Process
1. **CRITICAL**: List all files in `.issues/done/` to find the highest issue number
2. Use command: `ls .issues/done/ | sort -V | tail -5` to see the highest numbers
3. The next issue number = highest_number + 1

**Example:**
```
$ ls .issues/done/ | sort -V | tail -5
270-implement-issue-affects-codesymbol-link.md
271-implement-codesymbol-calls-impact-analysis.md
272-integrate-agent-must-comply-policy.md
273-implement-issue-resolved-by-commit.md

# Next issue should be: #274
```

---

## Phase 2: Read report.md

### Process
1. Read the file: `real-test/report.md`
2. Find all sections with `### FIND-###:` or `### BUG-###:` or `### DOC_GAP-###:` pattern
3. Extract:
   - ID (FIND-001, BUG-001, etc.)
   - Type (BUG, DOC_GAP, etc.)
   - Severity (HIGH, MEDIUM, LOW)
   - Title
   - Description

---

## Phase 3: Create Issues

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

### Naming Convention
- Filename format: `{issue_number}-{short-title}.md`
- Use kebab-case for the title
- Example: `274-workable-issues-endpoint-500-error.md`

---

## Phase 4: Update report.md

### Process
1. Add to report.md:
```
### Issues Created from Findings

| Issue | Title |
|-------|-------|
| #274 | [title FIND-001] |
| #275 | [title FIND-002] |
```

---

## Phase 5: Notify

### Output
Report to user:
```
Issues created:
- .issues/to-do/274-[slug].md
- .issues/to-do/275-[slug].md
```

---

## Example

### Input (report.md)
```markdown
### BUG-001: API returns wrong version

| Severity | HIGH |
|----------|------|
| Title | Version mismatch |

API returns 0.7.0 instead of 0.9.0
```

### Finding highest issue number
```
$ ls .issues/done/ | sort -V | tail -3
271-implement-codesymbol-calls-impact-analysis.md
272-integrate-agent-must-comply-policy.md
273-implement-issue-resolved-by-commit.md

# Next: #274
```

### Output (.issues/to-do/274-api-version-mismatch.md)
```markdown
# Issue #274: API returns wrong version

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

- [ ] Determine correct index from `.issues/done/` folder
- [ ] Read real-test/report.md
- [ ] Extract all FIND/BUG/DOC_GAP sections
- [ ] Create issue for each FINDING (not RESOLVED)
- [ ] Use correct sequential numbering from .issues/done/
- [ ] Update report.md with created issues
- [ ] Notify user of created issues

---

## Audio Notification

When workflow completes, play: `de find a issues.mp3`

See `.agent/skills/audio-notifications.md` for playback command.