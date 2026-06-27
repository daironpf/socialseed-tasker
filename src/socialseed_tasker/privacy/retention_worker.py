from __future__ import annotations
import os
import time
import threading
import tarfile
import tempfile
import json
from typing import Optional, Dict, Any
from socialseed_tasker.application.ports import StoragePort
from socialseed_tasker.privacy.policy import evaluate_policy

AUDIT_KEY = "privacy:audits"

class RetentionWorker:
    def __init__(self, container, interval: int = 3600):
        self.container = container
        self.storage: StoragePort = container.storage
        self.interval = int(os.getenv("TASKER_RETENTION_INTERVAL", str(interval)))
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _loop(self):
        while not self._stop.is_set():
            try:
                self.run_once()
            except Exception:
                pass
            time.sleep(self.interval)

    def run_once(self):
        issues = []
        if hasattr(self.container.issue_repo, "list_all"):
            issues = self.container.issue_repo.list_all()
        for i in issues:
            meta = {"kind": "issue", "created_at": i.get("created_at", int(time.time())), "tenant": i.get("tenant"), "tags": i.get("tags", [])}
            if not evaluate_policy(meta):
                self._archive_and_delete("issue", i.get("id"), i, meta)
        if hasattr(self.storage, "list_keys"):
            for k in self.storage.list_keys():
                if k.startswith(AUDIT_KEY):
                    continue
                meta = {"kind": "storage", "created_at": int(time.time()), "tenant": None, "tags": []}
                if not evaluate_policy(meta):
                    self._archive_and_delete("storage", k, None, meta)

    def _archive_and_delete(self, kind: str, key: str, record: Optional[Dict[str, Any]], meta: Dict[str, Any]):
        archive_enabled = os.getenv("TASKER_RETENTION_ARCHIVE", "0") == "1"
        archive_path = os.getenv("TASKER_RETENTION_ARCHIVE_PATH", os.path.join(tempfile.gettempdir(), "tasker-archives"))
        timestamp = int(time.time())
        audit = {"action": "delete", "kind": kind, "key": key, "timestamp": timestamp, "tenant": meta.get("tenant")}
        try:
            if archive_enabled:
                tmp = tempfile.mkdtemp(prefix="tasker-archive-")
                fname = f"{kind}-{key}-{timestamp}.json"
                with open(os.path.join(tmp, fname), "w", encoding="utf-8") as fh:
                    json.dump({"meta": meta, "record": record}, fh, indent=2)
                os.makedirs(archive_path, exist_ok=True)
                out = os.path.join(archive_path, f"{fname}.tar.gz")
                with tarfile.open(out, "w:gz") as tar:
                    tar.add(os.path.join(tmp, fname), arcname=fname)
            if kind == "issue" and hasattr(self.container.issue_repo, "delete"):
                self.container.issue_repo.delete(key)
            elif kind == "storage":
                self.storage.delete(key)
            self._write_audit(audit)
        except Exception as exc:
            audit["error"] = str(exc)
            self._write_audit(audit)

    def _write_audit(self, audit: Dict[str, Any]):
        try:
            raw = self.storage.get(AUDIT_KEY) or b"[]"
            arr = json.loads(raw.decode("utf-8")) if raw else []
            arr.append(audit)
            self.storage.put(AUDIT_KEY, json.dumps(arr).encode("utf-8"))
        except Exception:
            pass
