Tasker CLI

Usage
- python -m socialseed_tasker.cli.main <command> [flags]

Commands
- agent-context --issue-id <id> [--max-depth N]
- calculate-impact --issue-id <id> [--max-depth N]
- create-issue --id <id> --title <text> [--description <text>] [--status <text>]
- add-dependency --from <id> --to <id> [--relation <text>]
- parse-file --path <file>
- enqueue-task --task <name> --payload '<json>' [--token]
- task-status --task-id <id> [--token]

Output
- All successful responses are printed to stdout as a single JSON object and exit code 0.
- All errors are printed to stderr as a single JSON object with keys: status, command, error, details and exit code 2.

Examples
- python -m socialseed_tasker.cli.main create-issue --id issue-1 --title "Fix bug"
- python -m socialseed_tasker.cli.main agent-context --issue-id issue-1 --max-depth 3
