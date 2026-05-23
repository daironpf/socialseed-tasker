from __future__ import annotations
import hmac
import hashlib
import os
import json
import uuid
from typing import Dict, Optional, List
from socialseed_tasker.events.serializers import EventDTO
from socialseed_tasker.application.ports import StoragePort
from socialseed_tasker.application.exceptions import StorageError

class WebhookManager:
    SUBS_KEY = "webhook:subscriptions"

    def __init__(self, storage: StoragePort):
        self.storage = storage
        self._cache: Dict[str, Dict] = {}
        self._load_from_storage()

    def _load_from_storage(self):
        try:
            raw = self.storage.get(self.SUBS_KEY)
            if raw:
                self._cache = json.loads(raw.decode("utf-8"))
            else:
                self._cache = {}
        except Exception:
            self._cache = {}

    def _persist(self):
        try:
            self.storage.put(self.SUBS_KEY, json.dumps(self._cache).encode("utf-8"))
        except Exception as exc:
            raise StorageError(f"Failed to persist subscriptions: {exc}") from exc

    def create_subscription(self, url: str, events: Optional[List[str]] = None, secret: Optional[str] = None) -> Dict:
        sid = str(uuid.uuid4())
        sub = {"id": sid, "url": url, "events": events or ["*"], "secret": secret}
        self._cache[sid] = sub
        self._persist()
        return sub

    def list_subscriptions(self) -> List[Dict]:
        return list(self._cache.values())

    def get_subscription(self, sid: str) -> Optional[Dict]:
        return self._cache.get(sid)

    def delete_subscription(self, sid: str) -> None:
        if sid in self._cache:
            self._cache.pop(sid)
            self._persist()

    @staticmethod
    def verify_signature(secret: str, payload: bytes, signature_header: str, algo: str = "sha256") -> bool:
        if not secret:
            return False
        try:
            prefix = f"{algo}="
            if not signature_header.startswith(prefix):
                return False
            sig = signature_header[len(prefix):]
            mac = hmac.new(secret.encode("utf-8"), payload, getattr(hashlib, algo))
            expected = mac.hexdigest()
            return hmac.compare_digest(expected, sig)
        except Exception:
            return False

    def receive(self, raw_body: bytes, signature: Optional[str]) -> EventDTO:
        data = json.loads(raw_body.decode("utf-8"))
        event = EventDTO.from_dict(data)
        return event
