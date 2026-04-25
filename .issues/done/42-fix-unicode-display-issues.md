# Issue #42: Fix Rich table Unicode display issues in Windows terminal

## Description

When running CLI commands on Windows, the Rich table output displays incorrect characters for Unicode box drawing characters. The table headers show incorrect characters like "" instead of proper box characters.

### Requirements

- Ensure Rich tables render correctly in Windows terminal
- Consider using box profile that works across platforms or detect Windows and use compatible settings

### Technical Details

Test output observed:
```
| | Title                   | Stat | Prio | Component                     |
|---+-------------------------+-------+-------+-------------------------------|
```

The issue is likely due to Rich using Unicode box drawing characters that don't render correctly in Windows console.

### Solution Options

1. Use `box=box.SIMPLE` or `box=box.ASCII` for cross-platform compatibility
2. Set `console = Console(force_terminal=True)` with proper encoding
3. Use `BoxTable()` wrapper that selects appropriate box style based on environment

**Resolution**: Applied `box=SIMPLE` to `_issues_table()` and `_components_table()` functions in `commands.py` for cross-platform compatibility.

## Status: COMPLETED