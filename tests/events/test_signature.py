import hmac, hashlib
from socialseed_tasker.events.webhooks import WebhookManager
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage

def test_signature_verification():
    storage = MemoryStorage()
    wm = WebhookManager(storage)
    secret = "s3cr3t"
    payload = b'{"type":"test","payload":{"x":1}}'
    mac = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    header = "sha256=" + mac
    assert wm.verify_signature(secret, payload, header)
    assert not wm.verify_signature("bad", payload, header)
