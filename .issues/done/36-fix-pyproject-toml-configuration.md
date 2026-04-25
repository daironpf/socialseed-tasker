# Issue #36: Fix pyproject.toml invalid configuration

## Description

The `pyproject.toml` file has an invalid configuration under `[tool.setuptools.packages.find]`. The key `include-package-data` is not valid in this section.

### Error

```
configuration error: `tool.setuptools.packages`. must be valid exactly by one definition
```

When running `pip install -e .` the installation fails because setuptools cannot parse the configuration.

## Status: PENDING
