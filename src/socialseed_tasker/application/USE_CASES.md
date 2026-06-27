Use Cases GenerateAgentContext and CalculateImpact

Purpose
- calculate_impact(issue_id, max_depth, graph_repo) -> list[str]
  Deterministically returns sorted unique impacted issue ids.

- generate_agent_context(issue_id, max_depth, graph_repo, issue_repo, parser) -> dict
  Returns a JSON-serializable dict with keys:
    - issue: IssueDTO serialized as dict or null
    - impact_set: list of issue ids
    - related_code: mapping issue_id -> { files: { path: { symbols: [...], imports: [...] } } }
    - reasoning: list[str] deterministic trace of steps executed

Reasoning trace
- The reasoning list contains short deterministic messages describing each step.
- Use cases must append messages for start, load issue, calculate impact, parse files, and completion.

Examples
- calculate_impact("issue-b", 3, graph_repo)
- generate_agent_context("issue-b", 3, graph_repo, issue_repo, parser)
