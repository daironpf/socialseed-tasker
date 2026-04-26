# Issue #185: Enhance Documentation for PyPI Users

## Description

The documentation score is 8/10. While documentation is available, users installing from PyPI may not have access to the same rich documentation that exists in the GitHub repository.

## Problem

PyPI users get:
- Basic package installation
- CLI help (`tasker --help`)
- API docs (if they run the server)

But PyPI users lack:
- Quick start guide for end-users
- Examples specific to PyPI installation
- Links to full documentation

## Expected Behavior

When a user installs from PyPI, they should have a clear path to:
1. Getting started documentation
2. Configuration options
3. Examples

## Proposed Solutions

### 1. Improve PyPI Description
Update the long description on PyPI to be more comprehensive:
- Add quick start section
- Include configuration examples
- Add troubleshooting section

### 2. Create User Guide in Package
Include a user guide markdown file in the package:
```
socialseed_tasker/
  assets/
    user-guide.md  # Bundled user guide
```

### 3. CLI First-Run Message
Show a helpful message on first CLI run:
```bash
$ tasker --help
# ...existing help...
# 📚 Documentation: https://github.com/daironpf/socialseed-tasker#readme
# 💬 Issues: https://github.com/daironpf/socialseed-tasker/issues
```

## Status: COMPLETED

## Priority: LOW

## Component
Documentation

## Suggested Fix

Implement Solution #3 (CLI First-Run Message) for quick win:
1. Add footer to `--help` with links to docs
2. Optionally, create a `tasker docs` command that opens documentation

This would improve documentation_score from 8 to 9.

## Impact

- Better experience for PyPI users
- Clearer path to get help
- No breaking changes