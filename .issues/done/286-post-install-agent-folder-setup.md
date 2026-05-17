# Issue #286: Tasker Init Installs to .agent/tasker/ Directory

## Description
When running `tasker init`, all files should be installed inside `.agent/tasker/` folder instead of directly in `.agent/`. Additionally, an `Agent.md` file should be created in `.agent/` to document that all work must be done from the installation folder.

## Expected Behavior
- `tasker init` creates `.agent/tasker/` as the main agent configuration folder
- All template files (skills, workflows, configs, docker-compose, etc.) are copied inside `.agent/tasker/`
- A new `Agent.md` file is created in `.agent/` (root) establishing working directory rules for IA agents

## Actual Behavior
- Currently `tasker init` copies all files directly to `.agent/`
- No `Agent.md` file is created to document agent working directory

## Steps to Reproduce
1. Run: `tasker init`
2. Check: `.agent/` directory structure
3. Observe: All files are in `.agent/` root, not in `.agent/tasker/`
4. Observe: No `Agent.md` file exists in `.agent/`

## Status: RESOLVED

## Priority: HIGH

## Component
CLI / Scaffolding

## Technical Implementation
Modify `ScaffolderService` in `src/socialseed_tasker/core/system_init/scaffolder.py`:

1. Change default output directory from `.agent/` to `.agent/tasker/`
2. Ensure `Agent.md` is generated in `.agent/` root (not in tasker subfolder)
3. Update template paths and file operations

## Acceptance Criteria
- [ ] `tasker init` creates `.agent/tasker/` as main agent folder
- [ ] All existing templates (skills, workflows, configs, docker-compose, frontend) go into `.agent/tasker/`
- [ ] `Agent.md` is created in `.agent/` root
- [ ] `Agent.md` documents that all tasker work must be performed from `.agent/tasker/` directory
- [ ] Works with existing `--inplace` flag

## Agent.md Content Template
```markdown
# Tasker Agent Configuration

## Working Directory
ALL tasker work must be performed from: `.agent/tasker/`

## Directory Structure
```
./
├── .agent/
│   ├── tasker/       # <- WORK FROM HERE
│   │   ├── skills/
│   │   ├── workflows/
│   │   ├── configs/
│   │   ├── docker-compose.yml
│   │   └── frontend/
│   └── Agent.md      # This file
```

## Rules for IA Agents
1. Always `cd` to `.agent/tasker/` before running any tasker command
2. All file paths in tasker configuration are relative to `.agent/tasker/`
3. Code graph scans, RAG indexes, and logs are stored relative to this folder
4. Docker commands should be run from `.agent/tasker/`

## Commands Reference
```bash
cd .agent/tasker/
docker compose up -d
tasker issue list
```
```

## Impact
- Consistent agent working directory across all projects
- Clear separation between project root and agent configuration
- Improved agent IA workflow with explicit directory rules