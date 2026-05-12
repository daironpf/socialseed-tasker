# Workflow: Update Daily Log (Bitácora)

## When to Use

Use this workflow:
- At the end of a session or a major development block.
- When an issue is moved to `.issues/done/`.
- At the end of the day before pushing the final changes.

## Description

This workflow automates the creation and maintenance of the daily history file in `.history/`.

---

### Step 1: Collect Context
- [ ] Run `git status` to see modified files.
- [ ] Run `git log --oneline --since="today"` (if applicable).
- [ ] Identify which issues from `.issues/to-do/` or `.issues/done/` were touched.
- [ ] Review recent `pytest` outputs.

### Step 2: Prepare the Log Entry
- [ ] Check if `.history/YYYY-MM-DD.md` exists for the current date.
- [ ] If it doesn't exist, create it with the header `# YYYY-MM-DD`.
- [ ] Format the new activity following the structure in `skills/daily-log-management.md`.

### Step 3: Write to File
- [ ] Use `write_to_file` (if new) or `multi_replace_file_content` (if updating) to save the log.
- [ ] Ensure the "Summary" and "Project Progress" tables at the end of the file are updated to reflect the latest state.

### Step 4: Final Verification
- [ ] Verify that all issue numbers are correct.
- [ ] Ensure the file is valid Markdown.
- [ ] **Check for English-only content.**

---

## Example Summary Section
```markdown
## Summary
| Issue | Status | Priority | Tests |
|-------|--------|---------|------|
| #135 | ✅ DONE | HIGH | Passed |
| #136 | 🚧 WIP | MEDIUM | - |
```

---

## Audio Notification

When workflow completes, execute:

```bash
.venv/Scripts/python.exe .agent/assets/play_audio.py ".agent/assets/audios/Historial Actualizado.mp3"
```
