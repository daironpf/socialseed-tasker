from __future__ import annotations
import os
import time
from typing import Dict, Any

DEFAULT_RETENTION = {
    "issue": 60 * 60 * 24 * 365 * 3,
    "comment": 60 * 60 * 24 * 365 * 2,
    "log": 60 * 60 * 24 * 90,
    "storage": 60 * 60 * 24 * 365,
}

def get_retention_for(kind: str) -> int:
    env_key = f"TASKER_RETENTION_{kind.upper()}"
    v = os.getenv(env_key)
    if v:
        try:
            return int(v)
        except Exception:
            pass
    return DEFAULT_RETENTION.get(kind, 60 * 60 * 24 * 365)

def evaluate_policy(record_meta: Dict[str, Any]) -> bool:
    if not record_meta:
        return True
    tags = record_meta.get("tags", []) or []
    if "legal-hold" in tags:
        return True
    kind = record_meta.get("kind", "storage")
    created = record_meta.get("created_at", int(time.time()))
    age = int(time.time()) - int(created)
    retention = get_retention_for(kind)
    tenant = record_meta.get("tenant")
    if tenant:
        tkey = f"TASKER_RETENTION_{tenant}_{kind}".upper()
        tv = os.getenv(tkey)
        if tv:
            try:
                retention = int(tv)
            except Exception:
                pass
    return age < retention
