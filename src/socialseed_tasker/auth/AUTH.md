Authentication and RBAC

Configuration
- TASKER_AUTH_PROVIDER: 'inmemory' (default)
- TASKER_AUTH_USERS: JSON string mapping user_id -> {"token": "<token>", "permissions": ["perm1", ...]}
- TASKER_AUTH_TOKEN: default token used by CLI if --token not provided

Local dev users file
- src/socialseed_tasker/auth/users.json can be used to store example users for local development.

Default permissions
- create:issue
- delete:issue
- add:dependency
- read:context
- read:impact
- admin

CLI usage examples
- Create issue as admin:
  python -m socialseed_tasker.cli.main create-issue --id issue-1 --title "T" --token admintoken123

- Generate context as reader:
  python -m socialseed_tasker.cli.main agent-context --issue-id issue-1 --token readertoken123

Notes
- The InMemoryAuthProvider is intended for local development and CI. For production, implement a provider that verifies tokens against a secure identity provider.
