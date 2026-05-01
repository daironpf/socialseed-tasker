# Skill: Daily Log Management (Bitácora)

## Description

This skill defines the standards for maintaining the project's historical record in the `.history/` directory. Each file serves as a daily log (bitácora) of all significant activities, decisions, and progress made during a specific date.

---

## Log File Format

- **Filename**: `YYYY-MM-DD.md` (e.g., `2026-05-01.md`)
- **Title**: `# YYYY-MM-DD`

### Sections

1.  **Overview**: High-level summary of the day's focus (e.g., "v0.9.0 Documentation & Agent Knowledge").
2.  **Issues Resolved Today**: List of issue IDs (e.g., `#123, #124`).
3.  **Detailed Issue Breakdown**: For each issue worked on:
    - **Status**: COMPLETED / IN_PROGRESS / BLOCKED.
    - **Focus**: Brief technical goal.
    - **Changes**: Lists of files modified, new features, or docs updated.
    - **Git Commit**: The short hash and message (if available).
4.  **Summary Table**: A table summarizing the status and priority of the day's issues.
5.  **Project Progress**: A checklist of the current version's progress.
6.  **Commands Executed**: A list of key terminal commands run (git, pytest, tasker).
7.  **Notes**: Observations, technical debt identified, or plans for tomorrow.

---

## Data Gathering Rules

To populate the log accurately, the agent must:
- **Git History**: Use `git log --since="today"` to find commits.
- **Issue Files**: Check `.issues/to-do/` and `.issues/done/` for changes in status.
- **Test Results**: Capture the output of the latest `pytest` run.
- **File System**: Identify modified files using `git status` or by tracking its own edits.

---

## Rules for Updating

1.  **Incremental Updates**: If the file for today already exists, append new issue sections or update the summary. Do not overwrite previous entries from the same day.
2.  **Tone**: Professional, technical, and objective.
3.  **Consistency**: Ensure version numbers and issue IDs match the rest of the project.
4.  **Language**: All logs must be in **English**.
