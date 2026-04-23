# Issue #02: Entry Points on Windows Compatibility

## Description
After `pip install -e .`, the `tasker` and `socialseed-tasker` commands were not immediately available in the `Scripts` folder of the venv (needed to run via `python -m socialseed_tasker...`). This might be a Windows-specific behavior or an issue with Python 3.14.

## Expected Behavior
Entry points should be correctly generated and available in the PATH after installation across all operating systems and Python versions.

## Actual Behavior
Commands are not available in the Scripts folder on Windows, requiring workaround of running via `python -m socialseed_tasker...`.

## Steps to Reproduce
1. Install package with `pip install -e .` on Windows
2. Try to run `tasker` command directly
3. Observe command not found error
4. Must use `python -m socialseed_tasker...` instead

## Status: PENDING

## Priority: LOW

## Recommendations
- Verify entry point generation in the build process for different OS/Python versions
- Check setup.py or pyproject.toml entry point configuration
- Test on multiple Windows/Python combinations
- Consider using setuptools or ensuring proper script generation