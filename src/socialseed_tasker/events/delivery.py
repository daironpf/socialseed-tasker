from __future__ import annotations
import time
import json
import threading
import requests
from typing import Dict, Any, Optional
from socialseed_tasker.application.ports import StoragePort
from socialseed_tasker.events.serializers import EventDTO
from socialseed_tasker.application.exceptions import StorageError
from socialseed_tasker.observability.tracing import get_tracer

_tracer_fn = lambda: get_tracer("tasker.delivery")

DELIVERY_PREFIX = "webhook:delivery:"

class DeliveryWorker:
    def __init__(self, storage: StoragePort, max_retries: int = 5, base_backoff: float = 1.0):
        self.storage = storage
        self.max_retries = max_retries
        self.base_backoff = base_backoff
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run_loop(self):
        while not self._stop.is_set():
            try:
                self._process_pending()
            except Exception:
                pass
            time.sleep(1.0)

    def _process_pending(self):
        try:
            raw = self.storage.get("webhook:deliveries_index")
            index = json.loads(raw.decode("utf-8")) if raw else []
        except Exception:
            index = []
        for did in list(index):
            key = DELIVERY_PREFIX + did
            try:
                raw = self.storage.get(key)
                if not raw:
                    index.remove(did)
                    self.storage.put("webhook:deliveries_index", json.dumps(index).encode("utf-8"))
                    continue
                state = json.loads(raw.decode("utf-8"))
                if state.get("status") == "success":
                    self.storage.delete(key)
                    index.remove(did)
                    self.storage.put("webhook:deliveries_index", json.dumps(index).encode("utf-8"))
                    continue
                now = time.time()
                if now < state.get("next_attempt", 0):
                    continue
                self._attempt_delivery(did, state, key, index)
            except Exception:
                pass

    def _attempt_delivery(self, did: str, state: Dict[str, Any], key: str, index: list):
        with _tracer_fn().start_as_current_span("delivery.attempt"):
            url = state["url"]
            payload = state["payload"]
            headers = state.get("headers", {})
            try:
                r = requests.post(url, data=payload.encode("utf-8"), headers=headers, timeout=5)
                if 200 <= r.status_code < 300:
                    state["status"] = "success"
                    self.storage.put(key, json.dumps(state).encode("utf-8"))
                    return
                else:
                    raise Exception(f"status {r.status_code}")
            except Exception as exc:
                attempts = state.get("attempts", 0) + 1
                state["attempts"] = attempts
                if attempts >= self.max_retries:
                    state["status"] = "failed"
                else:
                    backoff = self.base_backoff * (2 ** (attempts - 1))
                    state["next_attempt"] = time.time() + backoff
                self.storage.put(key, json.dumps(state).encode("utf-8"))
                return

    def enqueue_delivery(self, url: str, payload: str, headers: Optional[Dict[str, str]] = None) -> str:
        with _tracer_fn().start_as_current_span("delivery.enqueue"):
            did = str(int(time.time() * 1000)) + "-" + str(hash(url))
            key = DELIVERY_PREFIX + did
            state = {
                "id": did,
                "url": url,
                "payload": payload,
                "headers": headers or {},
                "attempts": 0,
                "status": "pending",
                "next_attempt": time.time(),
            }
            try:
                self.storage.put(key, json.dumps(state).encode("utf-8"))
                raw = self.storage.get("webhook:deliveries_index")
                index = json.loads(raw.decode("utf-8")) if raw else []
                if did not in index:
                    index.append(did)
                    self.storage.put("webhook:deliveries_index", json.dumps(index).encode("utf-8"))
            except Exception as exc:
                raise StorageError(f"Failed to enqueue delivery: {exc}") from exc
            return did
