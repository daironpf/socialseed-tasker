# Issue #239: Increase test coverage for code-as-graph parser.py to 70%

## Description
The Tree-sitter code parser (parser.py) has only 31% test coverage with 374 statements and 258 missing lines. Many language-specific parsing paths are untested.

## Expected Behavior
Code parser should have comprehensive tests for all supported languages.

## Actual Behavior
Only 31% coverage - missing tests for:
- Java parsing
- C++ parsing
- AST traversal edge cases
- Multi-language scenarios

## Steps to Reproduce
1. Run: `pytest tests/ --cov=socialseed_tasker/core/code_analysis/parser.py`
2. Observe: Low coverage report

## Status: COMPLETED

## Priority: MEDIUM

## Component
CORE

## Suggested Fix
Add tests for:
- `test_parse_java_class`
- `test_parse_cpp_function`
- `test_ast_traversal_invalid_node`
- `test_multi_language_batch`

## Impact
Code-as-Graph features may fail for untested languages.

## Related Issues
- #124 (previous coverage effort)