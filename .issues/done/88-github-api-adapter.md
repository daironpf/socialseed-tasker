# Issue #88: GitHub API Adapter

## Description

Implement a Hexagonal Adapter to map Tasker Issues to GitHub Issues/Milestones. This is the core integration layer that translates between Tasker and GitHub domain models.

## Requirements

- Create GitHub adapter in `storage/adapters/github/`
- Implement IssueMapper: Tasker Issue <-> GitHub Issue conversion
- Implement MilestoneMapper: Tasker Project <-> GitHub Milestone conversion
- Support bidirectional mapping (Tasker -> GitHub, GitHub -> Tasker)
- Handle field translation (status, labels, assignees)
- Add rate limiting and retry logic for GitHub API calls
- Store GitHub metadata in Neo4j for sync tracking

## Technical Details

### Adapter Structure
```python
class GitHubAdapter(Protocol):
    def create_issue(self, issue: Issue) -> GitHubIssue: ...
    def get_issue(self, github_issue_id: int) -> Issue: ...
    def update_issue(self, issue: Issue) -> None: ...
    def create_milestone(self, project: Project) -> GitHubMilestone: ...
    def list_milestones(self) -> list[GitHubMilestone]: ...
```

### Configuration
- `GITHUB_TOKEN` - Personal Access Token
- `GITHUB_REPO` - Repository in format "owner/repo"
- `GITHUB_API_URL` - Custom GitHub instance URL (optional)

## Business Value

Enables synchronization between Tasker's graph-based issue management and GitHub's standard issue tracking.

## Status: COMPLETED