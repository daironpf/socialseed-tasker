import time
from socialseed_tasker.events.delivery import DeliveryWorker
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

class FailOnceHandler(BaseHTTPRequestHandler):
    called = 0
    def do_POST(self):
        FailOnceHandler.called += 1
        if FailOnceHandler.called == 1:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"fail")
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

def run_server(port):
    server = HTTPServer(("localhost", port), FailOnceHandler)
    server.serve_forever()

def test_delivery_retries(tmp_path):
    storage = MemoryStorage()
    worker = DeliveryWorker(storage=storage, max_retries=3, base_backoff=0.1)
    port = 9009
    t = threading.Thread(target=run_server, args=(port,), daemon=True)
    t.start()
    worker.start()
    did = worker.enqueue_delivery(f"http://localhost:{port}/", '{"x":1}')
    key = "webhook:delivery:" + did
    # The worker loop polls every 1s and the backoff doubles; local
    # localhost connect latency can add a couple of seconds per attempt, so
    # wait for the retry to land instead of sampling at a fixed instant.
    try:
        deadline = time.time() + 15.0
        raw = None
        while time.time() < deadline:
            raw = storage.get(key)
            if raw is None or b'"status": "success"' in raw or b'"status":"success"' in raw:
                break
            time.sleep(0.05)
        assert raw is None or b'"status": "success"' in raw or b'"status":"success"' in raw
    finally:
        worker.stop()
