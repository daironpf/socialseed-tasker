# Workflow: Test Project

## When to Use

When instructed to "prueba el proyecto" (test the project) or "test the project" by the user. This workflow should be triggered for comprehensive testing of all project functionality.

## Purpose

1. Rebuild project containers with latest code
2. Create a temporary test environment
3. Test all project features systematically
4. Identify bugs, issues, or improvements needed
5. Create actionable issues in `.issues/to-do/` for any problems found
6. Commit resolved issues and push to remote

## Prerequisites

- Python 3.10+ installed
- Git available
- Access to project source code
- Docker available

## Steps

### 1. Rebuild Docker Containers (Always Required)

```bash
# Navigate to project directory
cd <project_path>

# Stop any running containers
docker compose down

# Rebuild containers with latest code
docker compose build --no-cache

# Start containers
docker compose up -d

# Wait for services to be ready
sleep 10
```

### 2. Verify Services are Running

```bash
# Check container status
docker compose ps

# Test API health
curl -s http://localhost:8000/health
```

### 3. Setup Temporary Test Environment (Optional - for CLI testing)

```bash
# Create temporary directory
mkdir -p temp_test_<project_name>
cd temp_test_<project_name>

# Install project in development mode
pip install -e "<absolute_path_to_project>[dev]"
```

### 4. Test Core Functionality

Test each feature systematically:

#### For SocialSeed Tasker:
- **CLI Components**: create, list, show, update, delete
- **CLI Issues**: create, list, show, close, move, delete
- **CLI Dependencies**: add, remove, list, chain, blocked
- **CLI Analysis**: root-cause, impact
- **CLI System**: init, status
- **API Endpoints**: All REST endpoints if testable
- **Storage Backends**: Neo4j only (required)

#### Code-as-Graph Testing (Issue #208):
```bash
# Test API endpoint - scan repository
curl -X POST "http://localhost:8000/api/v1/code-graph/scan?repository_path=src&incremental=false"

# Test API endpoint - get files
curl -s "http://localhost:8000/api/v1/code-graph/files"

# Test API endpoint - get stats
curl -s "http://localhost:8000/api/v1/code-graph/stats"

# Test CLI command (if CLI container available)
docker exec tasker-api tasker code-graph scan /app --incremental
docker exec tasker-api tasker code-graph stats
```

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
# Remove temporary test directory (if created)
cd ..
rm -rf temp_test_<project_name>

# Optional: Stop containers after testing
# docker compose down
```

## Important Notes

- **ALWAYS rebuild containers** before testing - new code won't be available otherwise
- Use `docker compose build --no-cache` to ensure fresh code
- Always verify services are running before testing (`curl http://localhost:8000/health`)
- Test Code-as-Graph features by scanning the project itself
- Test with fresh data (don't use production data)
- Test both storage backends if possible (Neo4j required for most features)
- Verify all tests pass before considering testing complete
- Create clear, actionable issues with reproduction steps
- Follow project's commit conventions when making fixes

## Anti-Patterns to Avoid

- Testing only happy paths
- Not documenting failures
- Creating vague issues without clear steps
- Leaving temporary test files in the project
- Testing without verifying existing functionality still works