from __future__ import annotations
import time
import threading
import json
from typing import Optional, Dict, Any
from socialseed_tasker.application.ports import StoragePort
from socialseed_tasker.ml.runner import ModelRunner

JOBS_KEY = "ml:jobs"
RESULTS_PREFIX = "ml:results:"


class BatchWorker:
    def __init__(self, storage: StoragePort, runner: ModelRunner, poll_interval: float = 1.0):
        self.storage = storage
        self.runner = runner
        self.poll_interval = poll_interval
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
            time.sleep(self.poll_interval)

    def run_once(self):
        raw = self.storage.get(JOBS_KEY) or b"[]"
        jobs = json.loads(raw.decode("utf-8")) if raw else []
        if not jobs:
            return
        remaining = []
        for job in jobs:
            try:
                model = job["model"]
                features = job.get("features") or {}
                version = job.get("version")
                seed = job.get("seed")
                res = self.runner.predict(model, features, version=version, seed=seed)
                rid = f"{model}:{int(time.time() * 1000)}"
                self.storage.put(RESULTS_PREFIX + rid, json.dumps({"job": job, "result": res}).encode("utf-8"))
            except Exception:
                remaining.append(job)
        self.storage.put(JOBS_KEY, json.dumps(remaining).encode("utf-8"))
