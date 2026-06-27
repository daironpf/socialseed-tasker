# Issue #335: code_parser.py references undefined constants LANGUAGE_EXTENSIONS and TEST_PATTERNS

## Description

`src/socialseed_tasker/infrastructure/code_parser.py` references two module-level constants (`LANGUAGE_EXTENSIONS` and `TEST_PATTERNS`) that are never defined. This causes `NameError` at runtime, blocking all code-graph parsing functionality and breaking 25+ unit tests.

## Expected Behavior

The module should define `LANGUAGE_EXTENSIONS` as a `dict[str, str]` mapping file extensions to language names, and `TEST_PATTERNS` as a `list[re.Pattern]` of regex patterns for test file detection.

## Actual Behavior

```
Line 161: if ext in LANGUAGE_EXTENSIONS:
Line 169: return LANGUAGE_EXTENSIONS.get(ext, "unknown")
Line 217: is_test = any(pattern.match(file_path.name) for pattern in TEST_PATTERNS)
```

All three raise `NameError` because the constants were never defined.

## Steps to Reproduce

1. Run `pytest tests/unit/test_code_graph.py -q`
2. Observe `NameError: name 'LANGUAGE_EXTENSIONS' is not defined` on every test

## Status: PENDING

## Priority: HIGH

## Component

Infrastructure — `src/socialseed_tasker/infrastructure/code_parser.py`

## Suggested Fix

Add constants at module level after imports:

```python
LANGUAGE_EXTENSIONS: dict[str, str] = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".jsx": "javascript", ".tsx": "typescript", ".go": "go",
    ".rs": "rust", ".java": "java", ".cpp": "cpp", ".c": "c",
    ".h": "c", ".hpp": "cpp", ".rb": "ruby", ".swift": "swift",
    ".kt": "kotlin", ".scala": "scala", ".php": "php",
}

TEST_PATTERNS: list[re.Pattern] = [
    re.compile(r"^test_.*\.(py|js|ts|go|rs|java|cpp|c)$"),
    re.compile(r".*_test\.(py|js|ts|go|rs|java|cpp|c)$"),
    re.compile(r".*\.spec\.(js|ts|jsx|tsx)$"),
    re.compile(r".*\.test\.(js|ts|jsx|tsx)$"),
]
```

## Impact

Blocks all code-graph functionality (`tasker code-graph scan`, `tasker code-graph impact`) and fails 25+ unit tests.
