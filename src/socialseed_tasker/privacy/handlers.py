from __future__ import annotations
import os
import time
import tempfile
import tarfile
import json
from typing import Dict, Any


def export_subject(subject_id: str, container) -> str:
    tmp = tempfile.mkdtemp(prefix="tasker-export-subject-")
    files = []
    if hasattr(container.issue_repo, "list_by_subject"):
        issues = container.issue_repo.list_by_subject(subject_id)
    else:
        issues = [i for i in container.issue_repo.list_all() if i.get("owner") == subject_id]
    with open(os.path.join(tmp, "issues.json"), "w", encoding="utf-8") as fh:
        json.dump(issues, fh, indent=2)
    files.append("issues.json")
    storage = container.storage
    if hasattr(storage, "list_keys"):
        for k in storage.list_keys():
            if k.startswith(f"subject:{subject_id}:"):
                v = storage.get(k) or b""
                fname = k.replace(":", "_")
                with open(os.path.join(tmp, fname), "wb") as fh:
                    fh.write(v)
                files.append(fname)
    out = os.path.join(tempfile.gettempdir(), f"tasker-export-{subject_id}-{int(time.time())}.tar.gz")
    with tarfile.open(out, "w:gz") as tar:
        for f in files:
            tar.add(os.path.join(tmp, f), arcname=f)
    return out


def delete_subject(subject_id: str, container, dry_run: bool = True) -> Dict[str, Any]:
    to_delete = {"issues": [], "storage": []}
    if hasattr(container.issue_repo, "list_by_subject"):
        issues = container.issue_repo.list_by_subject(subject_id)
    else:
        issues = [i for i in container.issue_repo.list_all() if i.get("owner") == subject_id]
    for i in issues:
        iid = i.get("id")
        to_delete["issues"].append(iid)
        if not dry_run and iid and hasattr(container.issue_repo, "delete"):
            container.issue_repo.delete(iid)
    storage = container.storage
    if hasattr(storage, "list_keys"):
        for k in storage.list_keys():
            if k.startswith(f"subject:{subject_id}:"):
                to_delete["storage"].append(k)
                if not dry_run:
                    storage.delete(k)
    if not dry_run:
        try:
            raw = storage.get("privacy:audits") or b"[]"
            arr = json.loads(raw.decode("utf-8")) if raw else []
            arr.append({"action": "delete_subject", "subject": subject_id, "timestamp": int(time.time())})
            storage.put("privacy:audits", json.dumps(arr).encode("utf-8"))
        except Exception:
            pass
    return {"dry_run": dry_run, "result": to_delete}
