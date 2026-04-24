# Skill: Reporter

## Description
Provides persistent file writing capabilities for generating evaluation reports in `report.md`. Used for documenting findings during black-box testing.

---

## Capabilities

### 1. Report Structure

The report must follow this YAML schema:

```yaml
test_metadata:
  date: "YYYY-MM-DD"
  target_version: "0.8.0"
  use_case: "Description"
  requested_issues: 50
  created_issues: 0
  success_rate: "0%"

findings:
  - id: "FIND-001"
    type: "BUG | DOC_GAP | REFACTOR | FEATURE_REQ"
    component: "CLI | API | CORE | DOCKER | GRAPH_ENGINE"
    severity: "CRITICAL | HIGH | MEDIUM | LOW"
    title: "Concise title"
    description: "Technical explanation"
    evidence:
      log_trace: "Exact error"
      missing_info: "What was unclear"
    suggested_fix: "Technical proposal"
    impact: "How it affects autonomy"
    reproduction_steps:
      - "Command: ..."
      - "Payload: ..."
      - "Response: ..."

dx_evaluation:
  cli_intuition_score: 1-10
  error_message_clarity: 1-10
  documentation_score: 1-10
  api_clarity: 1-10
  setup_friction: 1-10
  agent_friction_points: []
```

### 2. Finding Types

| Type | Description |
|------|-------------|
| BUG | Code defect or unexpected behavior |
| DOC_GAP | Documentation inconsistency or missing info |
| REFACTOR | Technical debt or efficiency issue |
| FEATURE_REQ | Missing functionality |

### 3. Severity Levels

| Level | Criteria |
|-------|----------|
| CRITICAL | System unusable, data loss |
| HIGH | Major feature broken, workaround complex |
| MEDIUM | Feature impaired, easy workaround |
| LOW | Cosmetic, minor friction |

### 4. DX Evaluation Scores (1-10)

- **cli_intuition_score**: How intuitive the CLI is (especially for Chaos Monkey)
- **error_message_clarity**: Did error messages help fix the issue?
- **documentation_score**: Was documentation clear?
- **api_clarity**: Was API clear and consistent?
- **setup_friction**: How many steps to get running?

---

## Report Generation

### Create New Report

```python
def create_report(metadata, findings, dx_evaluation):
    content = f"""# Real-Test Evaluation Report

## Metadata

- Date: {metadata['date']}
- Version: {metadata['target_version']}
- Use Case: {metadata['use_case']}
- Requested Issues: {metadata['requested_issues']}
- Created Issues: {metadata['created_issues']}
- Success Rate: {metadata['success_rate']}

## Findings

{format_findings(findings)}

## DX Evaluation

{format_dx(dx_evaluation)}
"""
    write_file("real-test/report.md", content)
```

### Add Finding During Test

```python
def add_finding(
    finding_id,
    finding_type,
    component,
    severity,
    title,
    description,
    log_trace=None,
    missing_info=None,
    suggested_fix=None,
    impact=None,
    reproduction_steps=None
):
    # Format and append to findings section
    pass
```

---

## Usage

### Initial Report
```bash
echo "# Real-Test Evaluation Report" > real-test/report.md
```

### Append Finding
```bash
cat >> real-test/report.md << 'EOF'
### FIND-001: BUG - Missing endpoint

**Type**: BUG
**Component**: API
**Severity**: HIGH
...
EOF
```

---

## Output Location

- **Phase 3/4**: `real-test/report.md`
- **Cleanup**: Report stays in `real-test/` for review

---

## Best Practices

1. **Log in real-time**: Write findings as they occur
2. **Include evidence**: Copy exact log traces
3. **Be specific**: Exact reproduction steps
4. **Suggest fixes**: Don't just report, propose solutions