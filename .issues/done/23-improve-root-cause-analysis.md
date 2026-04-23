# Issue #23: Improve Root Cause Analysis with Graph Traversal

## Description

The current root cause analysis heuristic scoring is superficial. The `_calculate_graph_distance` method only traverses dependents (downstream), not dependencies (upstream), making it directional and incomplete. The "semantic overlap" is basic word intersection with stop word filtering, which produces false positives on common technical terms.

### Requirements

- Fix `_calculate_graph_distance` to traverse both directions (dependents AND dependencies)
- Replace simple word intersection with a weighted scoring that penalizes common technical terms (TF-IDF style)
- Add a maximum graph distance threshold (e.g., ignore issues beyond distance 3)
- Add a `min_confidence` parameter to filter out low-quality matches
- Write tests that verify graph distance calculation in both directions
- Write tests for edge cases: disconnected components, self-loops, deep chains

### Technical Details

File: `src/socialseed_tasker/core/project_analysis/analyzer.py`

Current `_calculate_graph_distance` only goes downstream:
```python
dependents = self._repository.get_dependents(current_id)  # Only one direction
```

Should traverse both:
```python
# Get both directions
dependents = self._repository.get_dependents(current_id)
dependencies = self._repository.get_dependencies(current_id)
all_connected = dependents + dependencies
```

For semantic scoring, add a technical term blacklist:
```python
TECHNICAL_STOP_WORDS = {
    "fix", "bug", "issue", "update", "change", "add", "remove",
    "the", "a", "an", "is", "to", "in", "of", "and", "for", "on",
    "test", "tests", "testing", "error", "exception", "failed",
}
```

Expected file paths:
- `src/socialseed_tasker/core/project_analysis/analyzer.py`
- `tests/unit/test_root_cause_analyzer.py`

### Business Value

More accurate root cause identification reduces debugging time. The current implementation would match any issue containing the word "test" or "error" with high confidence, which is useless noise.

## Status: COMPLETED
