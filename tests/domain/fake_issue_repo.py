"""In-memory fake IssueRepository for domain-level tests (no infrastructure)."""

from __future__ import annotations

from socialseed_tasker.application.dtos import IssueDTO, IssueSummary
from socialseed_tasker.application.repositories import IssueRepository


class FakeIssueRepository(IssueRepository):
    """In-memory issue store backed by a dict."""

    def __init__(self) -> None:
        self._data: dict[str, IssueDTO] = {}

    def save(self, issue: IssueDTO) -> None:
        self._data[issue.id] = issue

    def get(self, issue_id: str) -> IssueDTO | None:
        return self._data.get(issue_id)

    def list(self, status: str | None = None) -> list[IssueSummary]:
        result: list[IssueSummary] = []
        for issue in self._data.values():
            if status is None or issue.status == status:
                result.append(IssueSummary(id=issue.id, title=issue.title, status=issue.status))
        return result

    def delete(self, issue_id: str) -> None:
        self._data.pop(issue_id, None)
