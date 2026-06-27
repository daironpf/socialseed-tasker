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

## Note
This file was auto-generated during `tasker init`. Do not modify manually.
