# Issue #390: httpx INFO logging interleaved in CLI stdout/stderr output

## Description
Every CLI command that makes HTTP API calls (all commands when in `api` mode) emits httpx INFO-level log lines directly to the terminal. In PowerShell, these are treated as errors and displayed in red. The log lines are mixed with the actual command output, making the CLI hard to read and breaking JSON output parsing.

## Expected Behavior
httpx logging should be suppressed or redirected to a debug log file in normal operation. Only errors should be visible to the user.

## Actual Behavior
```
$ tasker status
tasker : {"timestamp": "...", "level": "INFO", "logger": "httpx", "message": "HTTP Request: GET ..."}
En línea: 1 Carácter: 1
+ tasker status
+ ~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: ...
    
[actual command output here]
```

## Steps to Reproduce
1. `tasker status` (or any command that hits the API)
2. Observe interleaved httpx log lines before the formatted output

## Root Cause
httpx logger is configured at INFO level globally, and no handler suppresses it for CLI usage. The logs go to stderr but are captured by PowerShell as error records.

## Status: PENDING

## Priority: LOW
