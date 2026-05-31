# Workflow: Convert Findings to Issues

## Trigger Command
`convert findings` or `findings to issues`

## Description
Converts findings in report.md to issues in `.issues/to-do/`. This workflow is executed after completing a project evaluation (black-box test).

---

## ⚠️ RULES

1. Only execute AFTER report.md is complete
2. DO NOT create issues for problems already resolved
3. **ALWAYS** use `.issues/done/` folder to determine the correct index (NOT the INDEX file in to-do)
4. The issue number must be the next sequential number after the highest numbered file in `.issues/done/`
5. After solving an issue (commit), move the file from `.issues/to-do/` to `.issues/done/` AND change its `## Status:` from `PENDING` to `COMPLETED`
6. INDEX files (`INDEX-*.md`) in `.issues/done/` are NOT issue files — skip them when finding highest number

---

## Phase 1: Determine Correct Issue Index

### Process
1. **CRITICAL**: List all files in `.issues/done/` to find the highest issue number
2. Use command (PowerShell):
   ```
   Get-ChildItem -Path ".issues/done" -Filter "*.md" -Name |
     Where-Object { $_ -match '^(\d+)' } |
     ForEach-Object { [int]$matches[1] } |
     Sort-Object -Descending |
     Select-Object -First 1
   ```
3. The next issue number = highest_number + 1

**Example (PowerShell):**
```
Get-ChildItem -Path ".issues/done" -Filter "*.md" -Name |
  Where-Object { $_ -match '^(\d+)' } |
  ForEach-Object { [int]$matches[1] } |
  Sort-Object -Descending |
  Select-Object -First 1
# Returns: 376
# Next issue should be: #377
```

**Linux/macOS alternative:**
```
ls .issues/done/ | grep -E '^[0-9]+' | sort -V | tail -1 | grep -oE '^[0-9]+'
```

---

## Phase 2: Read report.md

### Process
1. Read the file: `real-test/report.md`
2. Find all sections with `## Issues Found` (or `### FIND-###:`, `### BUG-###:`, `### DOC_GAP-###:`)
3. Extract:
   - Severity (HIGH, MEDIUM, LOW) — infer from context if not explicit
   - Title (short description)
   - Description (full detail, often bullet points after the title)
   - Suggested Fix (if mentioned)
   - Impact (if mentioned)
4. **Skip** findings that say "None" or "All previous findings resolved"

---

## Phase 3: Create Issues

### For Each FINDING

Create a new issue file in `.issues/to-do/` with:

```markdown
# Issue #XXX: [Title from Finding]

## Description
[Copy description from finding — full technical detail]

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Steps to Reproduce
1. [Concrete steps to reproduce the finding]

## Status: PENDING

## Priority: [LOW / MEDIUM / HIGH / CRITICAL]

## Component
[Affected component(s) — e.g. CLI, Neo4j repository, Scaffold, etc.]

## Suggested Fix
[Specific code-level suggestion from the finding, or leave empty if not known yet]

## Impact
[How this affects users or development workflow]

## Related Issues
- [Any related issue numbers, or "(none)"]

## Changes Made
[Leave empty — filled in after solving]

## Verification
[Leave empty — filled in after solving]
```

### Naming Convention
- Filename format: `{issue_number}-{kebab-case-title}.md`
- Use kebab-case (lowercase, hyphens for spaces)
- Example: `377-suppress-pydantic-serializer-warnings.md`

---

## Phase 4: Update report.md

### Process
1. Add a table right before `## Issues Found` in report.md:
```markdown
### Issues Created from Findings

| Issue | Title |
|-------|-------|
| #377 | Pydantic serializer warnings pollute --json output |
| #378 | [title of next finding] |
```

---

## Phase 5: After Solving an Issue

### Process
1. Change `## Status: PENDING` to `## Status: COMPLETED` in the issue file
2. Add details under `## Changes Made` and `## Verification`
3. Move the file from `.issues/to-do/` to `.issues/done/`:
   ```powershell
   Move-Item -Path ".issues/to-do/377-xxx.md" -Destination ".issues/done/377-xxx.md" -Force
   ```
4. Stage and commit:
   ```powershell
   git add "src/path/to/fix.py" ".issues/done/377-xxx.md"
   git commit -m "#377: Short description of the fix"
   ```

---

## Phase 6: Notify

### Output
Report to user:
```
Issues created:
- .issues/to-do/377-[slug].md
- .issues/to-do/378-[slug].md
```

---

## Example

### Input (report.md issues section)
```markdown
## Issues Found
- **Pydantic serializer warnings** in `issue list --json` output:
  `UserWarning: Pydantic serializer warnings` interleaved with JSON.
```

### Finding highest issue number (PowerShell)
```
Get-ChildItem -Path ".issues/done" -Filter "*.md" -Name |
  Where-Object { $_ -match '^(\d+)' } |
  ForEach-Object { [int]$matches[1] } |
  Sort-Object -Descending |
  Select-Object -First 1
# Returns: 376 -> Next: 377
```

### Output (.issues/to-do/377-suppress-pydantic-serializer-warnings.md)
```markdown
# Issue #377: Pydantic serializer warnings pollute --json output

## Description
`tasker issue list --json` produces pydantic serializer warnings
interleaved with JSON, breaking JSON consumers.

## Status: PENDING

## Priority: LOW
...
```

---

## Checklist

- [ ] Determine correct index from `.issues/done/` (skip INDEX-*.md)
- [ ] Read real-test/report.md
- [ ] Extract all findings from `## Issues Found` section
- [ ] Create issue file for each FINDING (not RESOLVED) in `.issues/to-do/`
- [ ] Use correct sequential numbering (highest in done + 1, +2, ...)
- [ ] Follow naming convention: `{number}-{kebab-title}.md`
- [ ] Update report.md with created issues table
- [ ] When solving: update status, add Changes Made, move to done, commit

---

## Audio Notification

When workflow completes, execute:

```bash
.venv/Scripts/python.exe .agent/assets/play_audio.py ".agent/assets/audios/de find a issues.mp3"
```