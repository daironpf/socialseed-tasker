# Workflow: Test Project

## When to Use

When instructed to "prueba el proyecto" (test the project) or "test the project" by the user. This workflow should be triggered for comprehensive testing of all project functionality.

## Purpose

1. Create a temporary test environment
2. Test all project features systematically
3. Identify bugs, issues, or improvements needed
4. Create actionable issues in `.issues/to-do/` for any problems found
5. Commit resolved issues and push to remote

## Prerequisites

- Python 3.10+ installed
- Git available
- Access to project source code

## Steps

### 1. Setup Temporary Test Environment

```bash
# Create temporary directory
mkdir -p temp_test_<project_name>
cd temp_test_<project_name>

# Install project in development mode
pip install -e "<absolute_path_to_project>[dev]"
```

### 2. Test Core Functionality

Test each feature systematically:

#### For SocialSeed Tasker:
- **CLI Components**: create, list, show, update, delete
- **CLI Issues**: create, list, show, close, move, delete
- **CLI Dependencies**: add, remove, list, chain, blocked
- **CLI Analysis**: root-cause, impact
- **CLI System**: init, status
- **API Endpoints**: All REST endpoints if testable
- **Storage Backends**: file, neo4j (if available)

### 3. Document Results

For each test, record:
- Command executed
- Expected behavior
- Actual behavior
- Pass/Fail status
- Error messages (if any)

### 4. Create Issues for Problems

If any issues are found, create files in `.issues/to-do/`:

```markdown
# Issue #{NN}-{kebab-case-title}.md

## Description

## Expected Behavior

## Actual Behavior

## Steps to Reproduce

## Status: PENDING
```

Use sequential numbering starting after the last issue in `.issues/done/`.

### 5. Fix Issues (Optional)

If issues are simple fixes, you may:
1. Fix the issue
2. Test the fix
3. Commit and push
4. Move issue to `.issues/done/`

### 6. Cleanup

```bash
# Remove temporary test directory
cd ..
rm -rf temp_test_<project_name>
```

## Important Notes

- Always test with fresh data (don't use production data)
- Test both storage backends if possible (file and neo4j)
- Verify all tests pass before considering testing complete
- Create clear, actionable issues with reproduction steps
- Follow project's commit conventions when making fixes

## Anti-Patterns to Avoid

- Testing only happy paths
- Not documenting failures
- Creating vague issues without clear steps
- Leaving temporary test files in the project
- Testing without verifying existing functionality still works