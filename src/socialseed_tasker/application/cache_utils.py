from __future__ import annotations
from typing import Callable, Optional, Any
import json
from socialseed_tasker.application.ports import StoragePort
from socialseed_tasker.application.exceptions import StorageError
from functools import wraps

def get_or_set(storage: StoragePort, key: str, factory: Callable[[], bytes], ttl_seconds: Optional[int] = None) -> bytes:
    try:
        v = storage.get(key)
    except Exception as exc:
        raise StorageError(f"Storage get failed for key {key}: {exc}") from exc
    if v is not None:
        return v
    val = factory()
    try:
        storage.put(key, val, ttl_seconds=ttl_seconds)
    except Exception as exc:
        raise StorageError(f"Storage put failed for key {key}: {exc}") from exc
    return val

def memoize(ttl_seconds: Optional[int] = None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            storage = kwargs.get("storage")
            if storage is None:
                return fn(*args, **kwargs)
            key_parts = [fn.__module__, fn.__name__, json.dumps(args, default=str, sort_keys=True), json.dumps(kwargs, default=str, sort_keys=True)]
            key = "cache:" + ":".join(key_parts)
            def factory():
                res = fn(*args, **kwargs)
                return json.dumps(res, default=str).encode("utf-8")
            raw = get_or_set(storage, key, factory, ttl_seconds=ttl_seconds)
            return json.loads(raw.decode("utf-8"))
        return wrapper
    return decorator
