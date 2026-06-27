# Issue #379: JSON output mixed with application logs

## Description
When using the `--json` flag on CLI commands (e.g., `tasker issue list --json`), the CLI outputs structured HTTP request log lines (from httpx) on stdout interleaved with the actual JSON payload. This breaks any consumer piping the output to `jq`, `ConvertFrom-Json`, or other JSON parsers.

## Expected Behavior
When `--json` is active, stdout should contain only valid, parseable JSON. Application/diagnostic logs should be routed to stderr.

## Actual Behavior
Running `tasker issue list --json` produces output like:
```
{"timestamp": "...", "level": "INFO", "logger": "httpx", "message": "HTTP Request: GET ... \"HTTP/1.1 200 OK\""}
[{"id": "...", "title": "...", ...}]
```
The JSON array is preceded by non-JSON log lines, making it unparseable by standard JSON tools.

## Steps to Reproduce
1. `tasker issue list -c "blog-platform" --json`
2. Observe httpx log lines before the JSON array
3. Attempt to pipe: `tasker issue list --json | python -m json.tool` → fails

## Status: PENDING

## Priority: MEDIUM

## Component
CLI, JSON output

## Suggested Fix
Route HTTP/application logs to stderr when `--json` flag is active, or configure httpx logger to only output to stderr. Ensure stdout contains only the requested JSON payload.

## Impact
Tools consuming stdout JSON directly (CI pipelines, scripts, AI agents) break when logs are interleaved with the payload.

## Related Issues
- #377 (Pydantic serializer warnings - similar stdout pollution issue, now fixed)

## Changes Made
Changed `StreamHandler(stream=sys.stdout)` to `StreamHandler(stream=sys.stderr)` in `src/socialseed_tasker/observability/logging.py:33`. This routes all JSON-formatted application/diagnostic logs to stderr, leaving stdout clean for structured output (JSON, Rich tables, etc.).

### Files modified
- `src/socialseed_tasker/observability/logging.py`: `configure_root_logger()` now writes to `sys.stderr` instead of `sys.stdout`

### Tests updated
- `tests/observability/test_logging.py::test_json_log_shape`: Replaced `capsys` approach with `io.StringIO` capture to avoid interference from logger initialization during import
- `tests/cli/test_cli_auth.py`: Added `_last_json_line()` helper to extract the JSON error line from stderr that now also contains log lines

## Verification
1. `tasker issue list --json` → stdout: `[]` (clean JSON), stderr: `{"timestamp":...,"level":"INFO","logger":"httpx",...}` (log lines)
2. `python -m pytest tests/observability/test_logging.py tests/cli/test_cli_auth.py` → 3 passed
3. Full test suite: 1026 passed, 8 failed (all pre-existing, unrelated)
4. Piping works: `tasker issue list --json | python -m json.tool` succeeds
