# Issue #49: Fix table column headers truncated in CLI output

## Description

Even with SIMPLE box enabled, the table column headers are still being truncated in the CLI output.

### Actual Output
```
| | Title                   | Stat | Prio | Component                     |
|---+-------------------------+-------+-------+-------------------------------|
```

### Expected Output
```
| ID    | Title                   | Status     | Priority  | Component                        |
|-------+-------------------------+------------+-----------+----------------------------------|
```

### Technical Details

The issue is that:
1. Headers are shortened to fit column width (e.g., "Status" -> "Stat")
2. The vertical bar at the start appears as "|" instead of proper box character

### Solution

1. Increase column widths to prevent truncation
2. Or ensure full header names are displayed
3. Investigate Rich table header rendering

**Resolution**: Modified `_issues_table()` and `_components_table()` functions:
- Increased minimum widths for better display
- Changed fixed widths to min_width where appropriate
- Added min_width to the Table constructor for overall width control
- Headers now display properly without truncation

## Status: COMPLETED