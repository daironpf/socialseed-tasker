"""GitHub API adapter for Tasker.

Implements hexagonal adapter pattern to map between Tasker issues
and GitHub issues/milestones.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

import httpx


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class GitHubIssue:
    """GitHub issue representation."""

    id: int
    number: int
    title: str
    body: str
    state: str
    labels: list[str]
    assignees: list[str]
    created_at: str
    updated_at: str
    closed_at: str | None
    html_url: str


@dataclass
class GitHubMilestone:
    """GitHub milestone representation."""

    id: int
    number: int
    title: str
    description: str
    state: str
    due_on: str | None


# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------


class RateLimiter:
    """Simple rate limiter for GitHub API calls."""

    def __init__(self, requests_per_second: float = 0.5) -> None:
        self._min_interval = 1.0 / requests_per_second
        self._last_call = 0.0

    def wait(self) -> None:
        """Wait if necessary to respect rate limits."""
        elapsed = time.time() - self._last_call
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call = time.time()


# ---------------------------------------------------------------------------
# GitHub Adapter
# ---------------------------------------------------------------------------


class GitHubAdapter:
    """Adapter for interacting with GitHub API.

    Implements hexagonal adapter pattern to translate between
    Tasker and GitHub domain models.
    """

    def __init__(
        self,
        token: str | None = None,
        repo: str | None = None,
        api_url: str | None = None,
    ) -> None:
        from socialseed_tasker.core.services.secret_manager import get_secret_manager

        sm = get_secret_manager()
        self._token = token or sm.get_github_token(repo or "") or os.environ.get("GITHUB_TOKEN", "")
        self._repo = repo or os.environ.get("GITHUB_REPO", "")
        self._api_url = api_url or os.environ.get("GITHUB_API_URL", "https://api.github.com")
        self._rate_limiter = RateLimiter()
        self._client = httpx.Client(
            headers={
                "Authorization": f"token {self._token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "socialseed-tasker",
            },
            timeout=30.0,
        )

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Make an API request with rate limiting and retry logic."""
        self._rate_limiter.wait()

        url = f"{self._api_url}/repos/{self._repo}{path}"

        for attempt in range(3):
            response = self._client.request(method, url, **kwargs)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                wait_time = max(reset_time - time.time(), 0) + 1
                time.sleep(wait_time)
                continue
            elif response.status_code >= 500:
                time.sleep(2**attempt)
                continue
            else:
                response.raise_for_status()

        response.raise_for_status()
        return {}

    def create_issue(
        self,
        title: str,
        body: str,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
    ) -> GitHubIssue:
        """Create a GitHub issue from Tasker issue."""
        data = self._request(
            "POST",
            "/issues",
            json={
                "title": title,
                "body": body,
                "labels": labels or [],
                "assignees": assignees or [],
            },
        )
        return GitHubIssue(
            id=data["id"],
            number=data["number"],
            title=data["title"],
            body=data["body"],
            state=data["state"],
            labels=[l["name"] for l in data.get("labels", [])],
            assignees=[a["login"] for a in data.get("assignees", [])],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            closed_at=data.get("closed_at"),
            html_url=data["html_url"],
        )

    def get_issue(self, issue_number: int) -> GitHubIssue:
        """Get a GitHub issue by number."""
        data = self._request("GET", f"/issues/{issue_number}")
        return GitHubIssue(
            id=data["id"],
            number=data["number"],
            title=data["title"],
            body=data["body"],
            state=data["state"],
            labels=[l["name"] for l in data.get("labels", [])],
            assignees=[a["login"] for a in data.get("assignees", [])],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            closed_at=data.get("closed_at"),
            html_url=data["html_url"],
        )

    def update_issue(
        self,
        issue_number: int,
        title: str | None = None,
        body: str | None = None,
        state: str | None = None,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
    ) -> GitHubIssue:
        """Update a GitHub issue."""
        update_data = {}
        if title is not None:
            update_data["title"] = title
        if body is not None:
            update_data["body"] = body
        if state is not None:
            update_data["state"] = state
        if labels is not None:
            update_data["labels"] = labels
        if assignees is not None:
            update_data["assignees"] = assignees

        data = self._request("PATCH", f"/issues/{issue_number}", json=update_data)
        return GitHubIssue(
            id=data["id"],
            number=data["number"],
            title=data["title"],
            body=data["body"],
            state=data["state"],
            labels=[l["name"] for l in data.get("labels", [])],
            assignees=[a["login"] for a in data.get("assignees", [])],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            closed_at=data.get("closed_at"),
            html_url=data["html_url"],
        )

    def create_milestone(
        self,
        title: str,
        description: str = "",
        due_on: str | None = None,
    ) -> GitHubMilestone:
        """Create a GitHub milestone."""
        data = self._request(
            "POST",
            "/milestones",
            json={
                "title": title,
                "description": description,
                "due_on": due_on,
                "state": "open",
            },
        )
        return GitHubMilestone(
            id=data["id"],
            number=data["number"],
            title=data["title"],
            description=data.get("description", ""),
            state=data["state"],
            due_on=data.get("due_on"),
        )

    def list_milestones(self, state: str = "open") -> list[GitHubMilestone]:
        """List GitHub milestones."""
        data = self._request("GET", f"/milestones?state={state}")
        return [
            GitHubMilestone(
                id=m["id"],
                number=m["number"],
                title=m["title"],
                description=m.get("description", ""),
                state=m["state"],
                due_on=m.get("due_on"),
            )
            for m in data
        ]

    def get_milestone(self, milestone_number: int) -> GitHubMilestone:
        """Get a specific milestone."""
        data = self._request("GET", f"/milestones/{milestone_number}")
        return GitHubMilestone(
            id=data["id"],
            number=data["number"],
            title=data["title"],
            description=data.get("description", ""),
            state=data["state"],
            due_on=data.get("due_on"),
        )

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def list_labels(self) -> list[dict]:
        """List all labels in the repository."""
        data = self._request("GET", "/labels")
        return [
            {
                "name": label["name"],
                "color": label.get("color", ""),
                "description": label.get("description", ""),
                "default": label.get("default", False),
            }
            for label in data
        ]
