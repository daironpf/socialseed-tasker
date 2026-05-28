from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urljoin

import httpx

from socialseed_tasker.application.actions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    InvalidEntityError,
    RemoteServiceError,
)

logger = logging.getLogger(__name__)


class ApiHttpClient:
    """Reusable HTTP client for communicating with the Tasker REST API.

    Encapsulates base URL, API key auth, timeouts, exponential backoff
    retries, health-check, pagination, and centralised error mapping
    from HTTP status codes to domain exceptions.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: int = 10,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            follow_redirects=True,
        )

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def health_check(self) -> bool:
        try:
            resp = self._client.get("/health", headers=self._headers())
            return 200 <= resp.status_code < 300
        except Exception as exc:
            logger.warning("Health check failed: %s", exc)
            return False

    def request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = path if path.startswith("/") else f"/{path}"
        try:
            resp = self._client.request(
                method,
                url,
                json=json,
                params=params,
                headers=self._headers(),
            )
            return self._handle_response(resp)
        except httpx.RequestError as exc:
            logger.debug("Request failed: %s", exc)
            raise RemoteServiceError(f"Connection error: {exc}")

    def _handle_response(self, resp: httpx.Response) -> Any:
        if 200 <= resp.status_code < 300:
            if resp.content:
                data = resp.json()
                if isinstance(data, dict) and "data" in data:
                    return data["data"]
                return data
            return None

        error_message = resp.text or f"HTTP {resp.status_code}"

        if resp.status_code == 400:
            raise InvalidEntityError(error_message)
        if resp.status_code == 401:
            raise AuthenticationError(error_message)
        if resp.status_code == 403:
            raise AuthorizationError(error_message)
        if resp.status_code == 404:
            return None
        if resp.status_code == 409:
            raise ConflictError(error_message)
        if resp.status_code >= 500:
            raise RemoteServiceError(f"Server error: {error_message}")

        raise RemoteServiceError(f"HTTP {resp.status_code}: {error_message}")

    def paginate(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        page_size: int = 50,
    ) -> list[dict[str, Any]]:
        page = 1
        all_items: list[dict[str, Any]] = []
        while True:
            p = dict(params or {})
            p.setdefault("page", page)
            p.setdefault("limit", page_size)
            data = self.request("GET", path, params=p)
            if not data:
                break
            if isinstance(data, dict):
                items = data.get("items", data.get("data", []))
            elif isinstance(data, list):
                items = data
            else:
                items = []
            all_items.extend(items)
            if isinstance(data, dict) and not data.get("next_page", False):
                break
            if isinstance(data, dict) and data.get("page", page) < page:
                break
            page += 1
        return all_items

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> ApiHttpClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
