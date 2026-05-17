# Workflow: Test Code

## When to Use
Before marking an issue as completed or submitting a pull request.

## Steps

### 1. Unit Testing
Run unit tests to verify individual components:
```bash
{test_commands}
```

### 2. Integration Testing
If the project has integration tests, run them to ensure components work together.

### 3. Manual Verification
If applicable, test the feature manually via CLI or API.

### 4. Regression Check
Ensure your changes haven't broken existing functionality.

### 5. Document Results
If any significant test results were found, log them in the issue reasoning:
```bash
tasker reasoning log --issue <ID> --thought "Tests passed with 95% coverage" --decision "Ready for release"
```
