# Issue #102: Add Input Validation and Sanitization Layer

## Description

The API does not validate or sanitize input for component names, issue titles, and descriptions. Special characters in these fields can cause issues with Neo4j queries and potential security vulnerabilities (XSS, injection).

## Requirements

- Add input validation for component names (no special characters that break Cypher)
- Add input validation for issue titles (length limits, character restrictions)
- Add input validation for issue descriptions
- Sanitize all user inputs before storing in Neo4j
- Add proper error messages for invalid inputs
- Create validation functions in a reusable module

## Technical Details

### Problematic Inputs
- Component names with: `"'<>;&`
- Issue titles longer than 200 characters
- HTML/script tags in descriptions

### Current Validation (if any)
- Issue title max length: 200 chars (enforced in Issue entity)
- Issue rejects empty title

### Needed Validations

**Component Name:**
- Max length: 100 characters
- Allowed: alphanumeric, dash, underscore, space
- Sanitize: escape quotes, remove HTML tags

**Issue Title:**
- Max length: 200 characters (already enforced)
- Required: non-empty
- Sanitize: escape quotes, remove control characters

**Issue Description:**
- Max length: 10000 characters
- Sanitize: remove dangerous HTML/JS, escape quotes

### Implementation Location
Create a new validation module:
```
src/socialseed_tasker/core/validation/
├── __init__.py
├── input_sanitizer.py      # Sanitization functions
├── validators.py           # Validation functions
└── exceptions.py            # Validation exceptions
```

### Example Usage
```python
from socialseed_tasker.core.validation import validate_component_name, sanitize_input

def create_component(name: str, project: str):
    validated_name = validate_component_name(name)
    sanitized_input = sanitize_input(validated_name)
    # Store in Neo4j
```

## Business Value

Input validation prevents:
- Neo4j query errors from special characters
- Potential XSS attacks via stored content
- Data corruption from oversized inputs
- Better error messages for users

## Status: COMPLETED