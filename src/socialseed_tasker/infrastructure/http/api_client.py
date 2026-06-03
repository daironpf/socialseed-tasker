from __future__ import annotations

import logging
import time
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
        timeout: int = 30,
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
        logging.getLogger("httpx").setLevel(logging.WARNING)

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
        for attempt in range(self.max_retries + 1):
            try:
                resp = self._client.request(
                    method,
                    url,
                    json=json,
                    params=params,
                    headers=self._headers(),
                )
                remaining = resp.headers.get("X-RateLimit-Remaining")
                if remaining is not None and int(remaining) <= 5:
                    logger.warning("Rate limit approaching: %s requests remaining", remaining)
                return self._handle_response(resp)
            except RemoteServiceError as exc:
                error_msg = str(exc)
                if "429" not in error_msg or attempt >= self.max_retries:
                    raise
                retry_after = 1
                import re
                match = re.search(r"Retry after (\d+)s", error_msg)
                if match:
                    retry_after = int(match.group(1))
                logger.warning("Rate limited (attempt %d/%d). Retrying in %ds...", attempt + 1, self.max_retries, retry_after)
                time.sleep(retry_after)
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

        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", "1"))
            raise RemoteServiceError(f"HTTP 429: Rate limited. Retry after {retry_after}s.")
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
            if isinstance(data, dict):
                pagination = data.get("pagination", {})
                if isinstance(pagination, dict):
                    if not pagination.get("has_next", False):
                        break
                elif not data.get("next_page", False):
                    break
            page += 1
            if page > 200:
                logger.warning("Paginate exceeded 200 pages, aborting")
                break
        return all_items

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> ApiHttpClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
