# Project Versions

## [1.0.1] - 2026-05-19

### v1.0.1 Checklist
- [x] **#001 Project Scaffolding:** Initial infrastructure injected by SocialSeed Tasker.
- [x] **#002 First Component:** Implementation of the first domain component.
- [x] **Dependency Enforcement:** Unit tests validating dependency closure rules.
- [x] **Real-Test Evaluation:** Black-box evaluation framework.
- [x] **DX Scores:** Developer Experience metrics documented.
- [x] **#285 Docker Windows Port Binding:** Updated docker-compose files to use 127.0.0.1:PORT:PORT format for Windows compatibility.
- [x] **#286 Agent Folder Setup:** tasker init now creates .agent/tasker/ as main folder and generates Agent.md in .agent/ root.
- [x] **#287 Agent Registration INTERNAL_ERROR:** Fixed parameter name mismatch (`createdAt` vs `created_at`) in Cypher query and Python code.
- [x] **#288 Policy Severity Warning:** Added `severity` property to CREATE_POLICY query and `_policy_to_dict()` function.
- [x] **Agent-Project Auto-linking:** Agents are now automatically assigned to project when only one project exists in Neo4j.
- [x] **CLI Bug Fix:** Added missing `import os` statement in commands.py.

### Release History
| Version | Date | Description |
|---------|------|-------------|
| 1.0.1   | 2026-05-19 | Bug Fixes & Agent Integration |
| 1.0.0   | 2026-05-04 | Full Autonomy Release |
