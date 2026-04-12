"""GitHub mirroring service for Tasker.

Provides functionality to mirror Tasker analysis results as comments
on linked GitHub issues.
"""

from __future__ import annotations

import os
import httpx


class GitHubMirroringService:
    """Service for mirroring Tasker analysis to GitHub issues."""

    def __init__(
        self,
        token: str | None = None,
        repo: str | None = None,
    ) -> None:
        self._token = token or os.environ.get("GITHUB_TOKEN", "")
        self._repo = repo or os.environ.get("GITHUB_REPO", "")
        self._api_url = "https://api.github.com"
        self._client = httpx.Client(
            headers={
                "Authorization": f"token {self._token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "socialseed-tasker",
            },
            timeout=30.0,
        )

    def post_comment(self, issue_number: int, body: str) -> dict:
        """Post a comment to a GitHub issue."""
        url = f"{self._api_url}/repos/{self._repo}/issues/{issue_number}/comments"
        response = self._client.post(url, json={"body": body})
        response.raise_for_status()
        return response.json()

    def update_comment(self, comment_id: int, body: str) -> dict:
        """Update an existing comment."""
        url = f"{self._api_url}/repos/{self._repo}/issues/comments/{comment_id}"
        response = self._client.patch(url, json={"body": body})
        response.raise_for_status()
        return response.json()

    def get_issue_comments(self, issue_number: int) -> list[dict]:
        """Get comments on a GitHub issue."""
        url = f"{self._api_url}/repos/{self._repo}/issues/{issue_number}/comments"
        response = self._client.get(url)
        response.raise_for_status()
        return response.json()

    def find_tasker_comment(self, issue_number: int) -> dict | None:
        """Find an existing Tasker analysis comment."""
        comments = self.get_issue_comments(issue_number)
        for comment in comments:
            if "Tasker Analysis" in comment.get("body", ""):
                return comment
        return None

    def mirror_root_cause(
        self,
        issue_number: int,
        analysis_data: dict,
    ) -> dict:
        """Mirror root cause analysis to GitHub."""
        body = self._format_root_cause_comment(analysis_data)

        existing = self.find_tasker_comment(issue_number)
        if existing:
            return self.update_comment(existing["id"], body)
        else:
            return self.post_comment(issue_number, body)

    def mirror_impact(
        self,
        issue_number: int,
        analysis_data: dict,
    ) -> dict:
        """Mirror impact analysis to GitHub."""
        body = self._format_impact_comment(analysis_data)

        existing = self.find_tasker_comment(issue_number)
        if existing:
            return self.update_comment(existing["id"], body)
        else:
            return self.post_comment(issue_number, body)

    def _format_root_cause_comment(self, data: dict) -> str:
        """Format root cause analysis as GitHub-flavored Markdown."""
        score = data.get("confidence", 0.0)
        reasons = data.get("reasons", [])
        primary_factor = data.get("primary_factor", "N/A")

        body = f"""## 🔍 Tasker Root Cause Analysis

### Analysis Result
- **Confidence Score**: {score:.2f}
- **Primary Factor**: {primary_factor}

### Contributing Factors
"""
        if reasons:
            for reason in reasons[:5]:
                body += f"- {reason}\n"
        else:
            body += "_No specific factors identified_\n"

        body += """
### Contributing Issues
"""
        for link in data.get("causal_links", [])[:5]:
            body += f"- [{link.get('issue_title', 'Unknown')}]({link.get('issue_id', '#')})\n"

        body += f"""
---
_Analysis performed by Tasker_
"""
        return body

    def _format_impact_comment(self, data: dict) -> str:
        """Format impact analysis as GitHub-flavored Markdown."""
        directly = len(data.get("directly_affected", []))
        transitively = len(data.get("transitively_affected", []))
        blocked = len(data.get("blocked_issues", []))
        risk = data.get("risk_level", "UNKNOWN")

        body = f"""## 🔍 Tasker Impact Analysis

### Impact Summary
- **Directly Affected**: {directly} issues
- **Transitively Affected**: {transitively} issues  
- **Blocked Issues**: {blocked} issues
- **Risk Level**: {risk}

### Affected Components
"""
        for comp in data.get("affected_components", [])[:5]:
            body += f"- {comp}\n"

        body += f"""
---
_Analysis performed by Tasker_
"""
        return body

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()
