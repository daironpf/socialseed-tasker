"""GitHub issue mapper service.

Provides mapping between Tasker UUIDs and GitHub issue numbers
with caching and rate limiting handling.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID


def _now() -> datetime:
    return datetime.now(timezone.utc)


class GitHubIssueMapper(Protocol):
    """Protocol for GitHub issue mapping."""

    def get_github_url(self, tasker_issue_id: str) -> str | None: ...
    def get_github_number(self, tasker_issue_id: str) -> int | None: ...
    def get_tasker_id(self, github_issue_number: int) -> str | None: ...
    def bulk_map(self, tasker_ids: list[str]) -> dict[str, int]: ...


class CachedGitHubIssueMapper:
    """GitHub issue mapper with in-memory caching."""

    def __init__(
        self,
        github_adapter=None,
        ttl_seconds: int = 300,
    ) -> None:
        self._adapter = github_adapter
        self._ttl = ttl_seconds
        self._cache: dict[str, tuple[int, datetime]] = {}
        self._reverse_cache: dict[int, str] = {}
        self._github_cache: dict[int, dict] = {}

    def set_github_adapter(self, adapter) -> None:
        """Set the GitHub adapter."""
        self._adapter = adapter

    def _is_fresh(self, timestamp: datetime) -> bool:
        """Check if cache entry is fresh."""
        age = (_now() - timestamp).total_seconds()
        return age < self._ttl

    def get_github_url(self, tasker_issue_id: str) -> str | None:
        """Get GitHub URL from Tasker issue ID."""
        number = self.get_github_number(tasker_issue_id)
        if number and self._adapter:
            repo = os.environ.get("GITHUB_REPO", "")
            return f"https://github.com/{repo}/issues/{number}"
        return None

    def get_github_number(self, tasker_issue_id: str) -> int | None:
        """Get GitHub issue number from Tasker ID."""
        if tasker_issue_id in self._cache:
            number, timestamp = self._cache[tasker_issue_id]
            if self._is_fresh(timestamp):
                return number

        if self._adapter:
            for gh_number, gh_data in self._github_cache.items():
                if gh_data.get("tasker_id") == tasker_issue_id:
                    self._cache[tasker_issue_id] = (gh_number, _now())
                    self._reverse_cache[gh_number] = tasker_issue_id
                    return gh_number

        return None

    def get_tasker_id(self, github_issue_number: int) -> str | None:
        """Get Tasker ID from GitHub issue number."""
        if github_issue_number in self._reverse_cache:
            return self._reverse_cache[github_issue_number]

        return self._github_cache.get(github_issue_number, {}).get("tasker_id")

    def bulk_map(self, tasker_ids: list[str]) -> dict[str, int]:
        """Map multiple Tasker IDs to GitHub numbers."""
        results = {}

        for tasker_id in tasker_ids:
            number = self.get_github_number(tasker_id)
            if number:
                results[tasker_id] = number

        return results

    def cache_github_issue(
        self,
        github_issue_number: int,
        tasker_issue_id: str,
        metadata: dict | None = None,
    ) -> None:
        """Cache a GitHub issue mapping."""
        self._cache[tasker_issue_id] = (github_issue_number, _now())
        self._reverse_cache[github_issue_number] = tasker_issue_id
        self._github_cache[github_issue_number] = {
            "tasker_id": tasker_issue_id,
            "metadata": metadata or {},
            "cached_at": _now().isoformat(),
        }

    def invalidate_cache(self, tasker_issue_id: str | None = None, github_issue_number: int | None = None) -> None:
        """Invalidate cache entries."""
        if tasker_issue_id and tasker_issue_id in self._cache:
            number, _ = self._cache.pop(tasker_issue_id)
            if number in self._reverse_cache:
                self._reverse_cache.pop(number, None)

        if github_issue_number and github_issue_number in self._github_cache:
            data = self._github_cache.pop(github_issue_number, {})
            tasker_id = data.get("tasker_id")
            if tasker_id and tasker_id in self._cache:
                self._cache.pop(tasker_id, None)

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        fresh_count = sum(1 for _, (_, ts) in self._cache.items() if self._is_fresh(ts))
        return {
            "total_entries": len(self._cache),
            "fresh_entries": fresh_count,
            "stale_entries": len(self._cache) - fresh_count,
            "reverse_cache_size": len(self._reverse_cache),
            "github_cache_size": len(self._github_cache),
        }


_mapper_instance: CachedGitHubIssueMapper | None = None


def get_github_issue_mapper() -> CachedGitHubIssueMapper:
    """Get the global GitHub issue mapper instance."""
    global _mapper_instance
    if _mapper_instance is None:
        ttl = int(os.environ.get("GITHUB_MAPPER_TTL_SECONDS", "300"))
        _mapper_instance = CachedGitHubIssueMapper(ttl_seconds=ttl)
    return _mapper_instance
