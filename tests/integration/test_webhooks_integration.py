import os
import socket
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

pytestmark = [
    pytest.mark.integration,
    pytest.mark.self_contained,
]

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
    server = HTTPServer(("127.0.0.1", port), EchoHandler)
    server.serve_forever()

def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")

def test_end_to_end_delivery():
    _skip_if_not_integration()
    storage = MemoryStorage()
    wm = WebhookManager(storage)
    bus = EventBus()
    port = int(os.getenv("TASKER_WEBHOOK_ECHO_PORT", "9010"))
    t = threading.Thread(target=run_echo, args=(port,), daemon=True)
    t.start()
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            socket.create_connection(("127.0.0.1", port), timeout=1).close()
            break
        except OSError:
            time.sleep(0.1)
    else:
        raise AssertionError("echo server did not start")
    worker = DeliveryWorker(storage)
    worker.start()
    sub = wm.create_subscription(url=f"http://127.0.0.1:{port}/", events=["test.event"], secret=None)
    e = {"id":"evt1","type":"test.event","payload":{"x":1}}
    event = wm.receive(json.dumps(e).encode("utf-8"), None)
    bus.publish(event)
    worker.enqueue_delivery(sub["url"], event.to_json(), headers={"Content-Type":"application/json"})
    deadline = time.time() + 15
    while time.time() < deadline and EchoHandler.last is None:
        time.sleep(0.2)
    assert EchoHandler.last is not None
    worker.stop()
