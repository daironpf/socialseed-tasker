# Skill: Programming Agent Governance

## Purpose
This skill defines how programming agents must operate within the Tasker ecosystem to maintain project governance, documentation integrity, and prevent code breakage.

## When to Use
This skill is automatically activated when:
- Executing TEST workflow (Phase 4: Implementation & Doc-Sync)
- Agent receives `WORK` command to implement issues
- Any programming agent needs to modify project code

---

## Core Rules

### 1. Issue Resolution Workflow

**Before writing any code:**
1. Fetch issue details from API: `GET /api/v1/issues/{id}`
2. Check for dependencies: `GET /api/v1/issues/{id}/dependencies`
3. Verify dependencies are CLOSED before starting
4. Read project policies: `GET /api/v1/policies`

**When implementing:**
1. Create a branch or working context
2. Implement the solution following hexagonal architecture
3. Run tests: `pytest` or `tasker test`
4. Verify no policy violations: `GET /api/v1/policies/validate`

**After implementation (REQUIRED):**
1. Close issue via API with reasoning:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/issues/{id}/close" \
     -H "Content-Type: application/json" \
     -d '{"resolution": "implemented", "reasoning": "..."}'
   ```
2. Add reasoning log:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/issues/{id}/reasoning" \
     -H "Content-Type: application/json" \
     -d '{"context": "implementation", "reasoning": "..."}'
   ```

---

### 2. Documentation Sync (MANDATORY)

**Every implementation MUST update documentation:**

| Document | Update Required |
|----------|-----------------|
| `ROADMAP.md` | Mark issue as RESOLVED in Known Issues table |
| `VERSIONS.md` | Add `[x]` to version checklist |
| `.issues/to-do/INDEX-*.md` | Update issue status to DONE |

**Update Process:**
```bash
# 1. Read current document
cat ROADMAP.md

# 2. Update with new content
# - Add "RESOLVED" status to issue
# - Update "Last updated" date

# 3. Commit changes (if applicable)
```

---

### 3. Policy Compliance

**Before any code change:**
1. Fetch active policies: `GET /api/v1/policies`
2. Analyze code impact: `tasker analyze --path src/`
3. Check for violations

**If policy violation detected:**
1. DO NOT proceed with implementation
2. Report violation as finding
3. Request policy exception or modification

**Policy Enforcement:**
- BLOCKER severity: Must fix before commit
- WARNING severity: Document and proceed
- INFO severity: Acknowledge in reasoning log

---

### 4. Breaking Changes Prevention

**Code Change Rules:**
1. NEVER modify entity schemas without migration
2. NEVER delete existing API endpoints
3. NEVER change field names without backward compatibility
4. ALWAYS run tests before closing issue

**Verification Commands:**
```bash
# Run tests
pytest tests/ -v

# Check API still works
curl http://localhost:8000/api/v1/components

# Verify no type errors
tasker lint
```

---

### 5. Tasker Endpoint Usage for Governance

All governance activities MUST use Tasker API:

```bash
# Issue Management
GET    /api/v1/issues                 # List all issues
GET    /api/v1/issues/{id}            # Get issue details
POST   /api/v1/issues                 # Create issue
POST   /api/v1/issues/{id}/close      # Close issue with resolution
POST   /api/v1/issues/{id}/dependencies # Add dependency
GET    /api/v1/issues/{id}/dependencies # Check dependencies

# Documentation
GET    /api/v1/projects/{id}/docs     # Get project docs
PUT    /api/v1/projects/{id}/docs     # Update docs

# Policies
GET    /api/v1/policies               # Get all policies
GET    /api/v1/policies/{id}         # Get policy details
POST   /api/v1/policies/validate     # Validate code against policies

# Code Analysis
POST   /api/v1/code/analyze          # Analyze code changes
GET    /api/v1/code/graph            # Get code dependency graph
```

---

## Implementation Count Guidelines

| Count | Use Case | Governance Strictness |
|-------|----------|----------------------|
| 0 | Issue creation only | Minimal |
| 1-5 | Basic doc-sync test | Standard |
| 10 | Full workflow test | HIGH |
| 20-30 | Stress test | MAXIMUM |

For counts >= 10:
- Run full policy check before each issue
- Update documentation after EVERY issue
- Verify no regressions after EACH close

---

## Agent Reasoning Log Template

When closing an issue, MUST include:

```json
{
  "context": "implementation",
  "reasoning": "Implementation approach and decisions",
  "related_nodes": ["component_id", "policy_ids"],
  "files_modified": ["file1.py", "file2.py"],
  "tests_passed": true,
  "policies_complied": true,
  "docs_updated": true
}
```

---

## Failure Modes

| Failure | Action |
|---------|--------|
| Policy violation | STOP, report as finding, DO NOT close issue |
| Tests failing | STOP, fix code, re-run tests |
| Doc sync missed | REVERT, update docs, re-close issue |
| Breaking change | REVERT immediately, report as HIGH finding |

---

## Integration with TEST Workflow

This skill is automatically loaded in Phase 4 of TEST workflow:

```
TEST Workflow
  → Phase 0: Requirements (use case, issues, etc.)
  → Phase 1: Environment Isolation
  → Phase 2: Infrastructure Init
  → Phase 3: Agent Evaluation (create issues)
  → Phase 4: Implementation & Doc-Sync ← ACTIVATES THIS SKILL
      - Select N issues (from Phase 0 implementation count)
      - For each issue:
        1. Fetch via API
        2. Check dependencies
        3. Implement (respecting policies)
        4. Run tests
        5. Update docs (ROADMAP.md, VERSIONS.md)
        6. Close with reasoning log
      - Verify all closed correctly
  → Phase 5: Report Generation
```

---

## Skill Activation

**Automatically activated when:**
- User runs `TEST` workflow
- Agent receives `WORK` command
- Any code modification is attempted

**Required permissions:**
- API read/write access
- File system read/write (docs)
- Test execution