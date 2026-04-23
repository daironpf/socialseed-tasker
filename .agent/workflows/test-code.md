# Workflow: Test Code

## When to Use

After implementing any code change, before committing.

## Prerequisites

The virtual environment must exist and have required packages:

```bash
.venv/Scripts/pip.exe install pydantic pytest
```

## Steps

### 1. Run All Tests

```bash
.venv/Scripts/python.exe -m pytest tests/ -v
```

### 2. Run Specific Test File

```bash
.venv/Scripts/python.exe -m pytest tests/unit/test_entities.py -v
```

### 3. Run with Coverage (when pytest-cov is installed)

```bash
.venv/Scripts/python.exe -m pytest tests/ --cov=socialseed_tasker --cov-report=term-missing
```

### 4. Run Only Failed Tests from Previous Run

```bash
.venv/Scripts/python.exe -m pytest tests/ --lf
```

## Test File Conventions

- Unit tests: `tests/unit/test_{module}.py`
- Integration tests: `tests/integration/test_{module}.py`
- E2E tests: `tests/e2e/test_{feature}.py`
- Test classes: `Test{ClassName}`
- Test functions: `test_{behavior_description}`

## Test Structure

```python
class TestComponent:
    def test_create_minimal_component(self):
        component = Component(name="Backend", project="my-project")
        assert component.name == "Backend"

    def test_component_is_frozen(self):
        component = Component(name="Backend", project="my-project")
        with pytest.raises(ValidationError):
            component.name = "Frontend"
```

## Important Notes

- `conftest.py` adds `src/` to `sys.path` so imports work
- All tests must pass before any commit
- Write tests that verify both happy path and edge cases
- Test immutability, validation, and serialization for entities
