# Issue #202 - Unicode Parsing Issue in API

## Description

When sending JSON with non-ASCII characters (e.g., Spanish accented characters like "Gestión", "Clínicas"), the API returns "There was an error parsing the body". ASCII-only text works correctly.

## Status: COMPLETED (NOT A BUG)

## Priority

**N/A** - Not an API bug, but added test coverage

## Component

API, Testing

## Investigation Results

### Root Cause

**The API works correctly with Unicode.** The issue was with Windows terminal/bash encoding, not the API itself.

### Testing Evidence

1. **File-based JSON test**:
   ```bash
   cat > test.json << 'EOF'
   {"description": "Gestión de citas con clínicas"}
   EOF
   curl -X POST http://localhost:8000/api/v1/components -d @test.json
   # Returns: 201 Created with correct Unicode
   ```

2. **Python requests test**:
   ```python
   requests.post(url, json={"description": "Gestión de clínicas"})
   # Status: 201 - API accepts Unicode correctly
   ```

3. **Verification of stored data**:
   ```bash
   curl http://localhost:8000/api/v1/components/{id}
   # Returns: "Gestión de citas con clínicas" - stored correctly
   ```

### Why curl failed on Windows

Windows PowerShell/CMD uses legacy encoding (CP1252 or similar) for command-line arguments. When you pass Unicode directly in `-d`, the encoding may be corrupted before reaching the API.

## Changes Made

### Added Unicode Test Coverage

Added `TestUnicodeAndInternationalization` class to `tests/unit/test_api.py`:

1. `test_create_component_with_spanish_accents` - Spanish accented characters
2. `test_create_issue_with_spanish_accents` - Issue creation with accents
3. `test_create_issue_with_emoji` - Emoji support in titles and descriptions
4. `test_create_issue_with_international_characters` - Chinese, Russian, Arabic
5. `test_update_issue_with_unicode` - Update operations with Unicode

## Verification

### Ruff Check
```bash
$ python -m ruff check src/
All checks passed!
```

### Tests
```bash
$ python -m pytest tests/unit/test_api.py::TestUnicodeAndInternationalization -v
5 passed in 3.33s

$ python -m pytest tests/unit/ -q
459 passed, 1 skipped, 1 warning in 21.76s
```

## Impact

- **API**: Correctly handles UTF-8 encoded JSON (no code changes needed)
- **Documentation**: Added note about using files for Unicode in curl on Windows
- **Testing**: 5 new tests for internationalization coverage

## Recommendations

For Windows users using curl with Unicode:

1. **Use file input**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/issues -d @data.json
   ```

2. **Use Python/requests** instead of curl for complex payloads

3. **Set UTF-8 encoding** in terminal:
   ```powershell
   [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
   chcp 65001
   ```

## Related Issues

- Real-Test Evaluation: FIND-001 (Dental Clinic System)
- This was a terminal encoding issue, not an API bug