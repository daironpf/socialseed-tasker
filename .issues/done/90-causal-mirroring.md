# Issue #90: Causal Mirroring

## Description

Implement automated sync of Tasker's "Analysis" (Root Cause/Impact) as comments in GitHub Issues for human reviewers. When analysis is run in Tasker, the results are posted as comments in the linked GitHub issue.

## Requirements

- Add "GitHub Issue Link" field to Issue entity
- Create link via API or CLI: `tasker issue link --github 123`
- Run analysis: `POST /analyze/root-cause` or `/analyze/impact/{id}`
- Format analysis results as GitHub-flavored Markdown
- Post as comment on linked GitHub issue
- Update comment if analysis is re-run
- Add configuration for auto-mirror (on/off per project)

## Technical Details

### Issue Enhancement
```python
class Issue(BaseModel):
    github_issue_url: str | None = None  # e.g., "https://github.com/owner/repo/issues/123"
    github_issue_number: int | None = None
    last_mirrored_at: datetime | None = None
```

### Comment Format
```markdown
## 🔍 Tasker Analysis

### Root Cause Analysis
- **Score**: 0.85
- **Primary Factor**: Component mismatch (backend vs frontend)
- **Related Issues**: #45, #67

### Impact Analysis  
- **Direct Dependents**: 3 issues
- **Risk Level**: HIGH
- **Blocked Issues**: 2

_Analysis performed by Tasker_
```

## Business Value

Human reviewers in GitHub can see Tasker's graph analysis without leaving GitHub. Bridges the gap between AI analysis and human oversight.

## Status: COMPLETED