# Issue #101: Redis storage tests patch module attribute that doesn't exist

## Description

`tests/infrastructure/test_redis_storage_unit.py` patches `socialseed_tasker.infrastructure.redis_storage.redis`, but the `redis` package may not be installed. The module imports `redis` inside a `try/except` block:

```python
try:
    import redis
    _REDIS_AVAILABLE = True
except Exception:
    _REDIS_AVAILABLE = False
```

If the `redis` package is not installed, the import fails and `redis` is never bound as a module attribute, causing `AttributeError` when the test tries to patch it.

## Expected Behavior

Tests should either:
1. Install `redis` as a dev/test dependency, or
2. Use a more robust patching strategy that doesn't depend on the import succeeding

## Actual Behavior

```
AttributeError: <module 'socialseed_tasker.infrastructure.redis_storage'>
does not have the attribute 'redis'
```

## Steps to Reproduce

1. Ensure `redis` package is NOT installed
2. Run `pytest tests/infrastructure/test_redis_storage_unit.py -q`
3. Observe `AttributeError` on both tests

## Status: PENDING

## Priority: MEDIUM

## Component

Tests — `tests/infrastructure/test_redis_storage_unit.py`

## Suggested Fix

Add `redis` to `[project.optional-dependencies] dev` in `pyproject.toml`, or refactor the test to mock at a different level (e.g. patch `redis.from_url` directly using `sys.modules`).

## Impact

2 tests fail when `redis` package is not installed in the development environment.
