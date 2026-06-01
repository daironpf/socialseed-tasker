# Issue #377: Pydantic serializer warnings pollute --json output

## Description
`tasker issue list --json` produces pydantic serializer warnings (`UserWarning: Pydantic serializer warnings`) that get interleaved with the JSON output. This makes the JSON output non-parseable for consumers expecting clean JSON.

## Expected Behavior
JSON output (via `--json` flag) should be clean, parseable JSON with no warning messages interleaved.

## Actual Behavior
Running `tasker issue list -c "e-commerce" --json` produces:
```
{"timestamp": "...", "level": "INFO", "logger": "neo4j_driver", ...}
UserWarning: Pydantic serializer warnings:
  - `description_embedding` is a union field like `str | None | list` and...
<JSON array>
```

The `UserWarning` line breaks JSON consumers that read stdout.

## Steps to Reproduce
1. Create a component with issues
2. Run `tasker issue list --json`
3. Observe pydantic `UserWarning` interleaved in stdout

## Status: PENDING

## Priority: LOW

## Component
CLI, Issue listing

## Suggested Fix
Suppress pydantic serializer warnings in JSON output mode. Either:
- Configure pydantic to not warn during serialization (`model_config` with `ser_json_timedelta` and related settings)
- Redirect warnings to stderr when `--json` mode is active
- Use `warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")` before serialization

## Impact
Low. The JSON output is still produced (after the warning line), but tools consuming the JSON directly from stdout may break. Human users reading the table format are unaffected.

## Related Issues
- (none)
