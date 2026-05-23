import os
import threading
import time
import requests
import json
import pytest
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage
from socialseed_tasker.events.webhooks import WebhookManager
from socialseed_tasker.events.delivery import DeliveryWorker
from socialseed_tasker.events.bus import EventBus
from http.server import BaseHTTPRequestHandler, HTTPServer

pytestmark = pytest.mark.integration

class EchoHandler(BaseHTTPRequestHandler):
    last = None
    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        EchoHandler.last = body.decode("utf-8")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

def run_echo(port):
    server = HTTPServer(("localhost", port), EchoHandler)
    server.serve_forever()

def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")

def test_end_to_end_delivery():
    _skip_if_not_integration()
    storage = MemoryStorage()
    wm = WebhookManager(storage)
    bus = EventBus()
    worker = DeliveryWorker(storage)
    worker.start()
    port = 9010
    t = threading.Thread(target=run_echo, args=(port,), daemon=True)
    t.start()
    sub = wm.create_subscription(url=f"http://localhost:{port}/", events=["test.event"], secret=None)
    e = {"id":"evt1","type":"test.event","payload":{"x":1}}
    event = wm.receive(json.dumps(e).encode("utf-8"), None)
    bus.publish(event)
    worker.enqueue_delivery(sub["url"], event.to_json(), headers={"Content-Type":"application/json"})
    time.sleep(1.0)
    assert EchoHandler.last is not None
    worker.stop()
