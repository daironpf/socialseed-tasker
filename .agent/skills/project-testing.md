# Skill: Project Testing Workflow

## Description

This skill enables AI agents to perform comprehensive testing of the SocialSeed Tasker project. When the user says "prueba el proyecto" or "test the project", this workflow should be triggered.

## Trigger Phrases

- "prueba el proyecto"
- "test the project"
- "test all functionality"
- "probar el proyecto"
- "verify project works"

## What This Skill Does

1. **Creates temporary environment**: Sets up isolated test directory
2. **Tests all features**: CLI commands, API endpoints, storage backends
3. **Documents results**: Records pass/fail for each test
4. **Creates issues**: Generates actionable issues in `.issues/to-do/` for any problems
5. **Optionally fixes**: Can fix simple issues and commit them
6. **Cleans up**: Removes temporary files after testing

## Key Conventions

- **Issue numbering**: Continue from last issue in `.issues/done/`
- **Issue format**: `{NN}-{kebab-case-title}.md`
- **Commit style**: Use conventional commits (feat:, fix:, etc.)
- **Testing approach**: Test both file and neo4j backends when possible

## Usage

When user asks to test the project:
1. Read `.agent/workflows/test-project.md` for detailed steps
2. Follow the workflow to test all functionality
3. Create issues for any problems found
4. Optionally fix simple issues and commit them
5. Report summary of test results

## Related Files

- `.agent/workflows/test-project.md` - Detailed workflow
- `.agent/workflows/implement-issue.md` - How to fix created issues
- `.agent/workflows/commit-push.md` - How to commit fixes