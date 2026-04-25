# Issue #40: CLI output truncation with Unicode characters

## Description

When running `tasker issue list` and `tasker dependency blocked`, the table output shows truncated data due to character encoding issues with Unicode symbols in the status and priority columns.

### Observed behavior

```
| ID | Title                    | Sta� | Pri� | Component                     |
```

The status (OPEN/CLOSED) and priority (LOW/MEDIUM/HIGH/CRITICAL) columns show garbled characters (�) instead of proper display.

### Root cause

The Rich Table is using default encoding that doesn't properly handle Unicode characters on Windows console.

### Expected behavior

All characters should display correctly without truncation or replacement characters.

## Status: PENDING
