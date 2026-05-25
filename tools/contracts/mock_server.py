from __future__ import annotations

import json
import os
import threading
from typing import Any

import uvicorn
from fastapi import FastAPI, Response

from .openapi import extract_endpoints, generate_example, load_spec


class MockServer:
    def __init__(
        self,
        spec_path: str,
        port: int = 9000,
        overrides_dir: str | None = None,
        seed: int = 42,
    ):
        self.spec_path = spec_path
        self.port = int(port)
        self.overrides_dir = overrides_dir
        self.seed = int(seed)
        self.app = FastAPI(title="Contract Mock Server")
        self._server_thread: threading.Thread | None = None
        self._setup_routes()

    def _load_override(self, method: str, path: str) -> dict | None:
        if not self.overrides_dir:
            return None
        fname = f"{method}_{path.strip('/').replace('/', '_')}.json"
        p = os.path.join(self.overrides_dir, fname)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as fh:
                return json.load(fh)
        return None

    def _setup_routes(self) -> None:
        spec = load_spec(self.spec_path)
        eps = extract_endpoints(spec)
        for e in eps:
            method = e["method"].lower()
            path = e["path"]
            schema = e.get("response_schema")
            example = generate_example(schema, seed=self.seed)
            override = self._load_override(e["method"], path)
            body = override if override is not None else example

            async def handler(response_body: dict = body) -> Response:
                return Response(
                    content=json.dumps(response_body),
                    media_type="application/json",
                )

            self.app.add_api_route(path, handler, methods=[method])

    def start(self) -> None:
        if self._server_thread and self._server_thread.is_alive():
            return

        def run() -> None:
            uvicorn.run(
                self.app, host="0.0.0.0", port=self.port, log_level="warning"
            )

        self._server_thread = threading.Thread(target=run, daemon=True)
        self._server_thread.start()

    def stop(self) -> None:
        pass
