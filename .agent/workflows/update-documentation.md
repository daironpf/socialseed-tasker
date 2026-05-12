# Workflow: Update Project Documentation

## When to Use

Use this workflow when:
- Completing an issue that changes functionality, architecture, or interfaces.
- Preparing a new release (vX.X.X).
- Refactoring code that affects internal logic or public APIs.
- Adding new agent skills or workflows.

## Description

This workflow ensures that documentation remains the "Single Source of Truth" across all levels: from docstrings in the source code to the markdown files used for project management, agentic guidance, and PyPI distribution.

---

## Phase 1: Code-Level Documentation (Source Code)

### 1. Update Docstrings
- **Location**: `src/socialseed_tasker/`
- **Action**: Review all modified functions, classes, and methods.
- **Rules**:
    - Use Google-style or ReST docstrings.
    - Document parameters (`Args`), return values (`Returns`), and exceptions (`Raises`).
    - Ensure type hints are accurate.
- **Checklist**:
    - [ ] Do all new public methods have docstrings?
    - [ ] Are parameter descriptions up to date?
    - [ ] Does the `core/` logic explain the business rules?

### 2. Update Comments
- **Action**: Explain "Why" something is done, not "What" (the code says what).
- **Rules**:
    - Remove stale comments.
    - Document complex algorithms or Neo4j Cypher queries.

---

## Phase 2: Project-Level Documentation (Markdown)

### 1. Update `project.md` (The Blueprint)
- **Action**: Update the core architecture, domain model, or CLI/API interface sections if structural changes occurred.
- **Reference**: See `skills/project-documentation.md`.

### 2. Update `README.md` & `API_REFERENCE.md`
- **Action**:
    - Add new CLI command examples.
    - Update the REST API endpoint tables.
    - Update environment variable descriptions.

### 3. Update Release Tracking (`ROADMAP.md`, `VERSIONS.md`, `CHANGELOG.md`)
- **Action**:
    - Mark issues as resolved in `ROADMAP.md`.
    - Check off items in the `VERSIONS.md` checklist.
    - Add a concise entry to `CHANGELOG.md` under the current version.

---

## Phase 3: Agentic Documentation (`.agent/`)

### 1. Update Skills and Workflows
- **Location**: `.agent/skills/` and `.agent/workflows/`
- **Action**:
    - If a new architectural pattern is introduced, create/update a `.md` in `skills/`.
    - If a process changes (e.g., how to run tests), update the corresponding `workflow`.
- **Consistency Check**:
    - Run `grep -r "v0.8.0" .agent/` to ensure no outdated version references remain.
    - Ensure all instructions are in English.

---

## Phase 4: Distribution & PyPI Documentation

### 1. Asset Synchronization
- **Location**: `src/socialseed_tasker/assets/`
- **Action**: If you changed how `tasker init` works or updated the scaffold templates, ensure these files are updated.
- **Context**: These are the files that users will see when they run the tool after installing it from PyPI.

### 2. PyPI Metadata
- **File**: `pyproject.toml`
- **Action**: Verify version and description.

---

## Phase 4b: Tasker Init Templates Documentation

When updating documentation, ALWAYS check and update the templates installed during `tasker init`. These templates become the user's first experience with the project.

### 1. Core Templates to Check
- **Location**: `src/socialseed_tasker/assets/templates/`

| Template File | Purpose | When to Update |
|---------------|---------|----------------|
| `AGENT_GUIDE.md` | Agent protocol and commands | New agent features, CLI commands |
| `README.md` | Agent skills overview | New skills or workflows |
| `project.md` | Project architecture template | Architecture changes |
| `project.json` | Machine-readable project metadata | New metadata fields |
| `VERSIONS.md` | Release tracking template | Version changes |
| `ROADMAP.md` | Project roadmap template | New features planned |
| `policies.md` | Default governance policies | New policy rules |
| `workflows/*.md` | Step-by-step procedural guides | Process changes |
| `skills/*.json` | Agent skill manifests | New skills |
| `skills/task_skill.py` | Python skill functions | New capabilities |

### 2. Update Checklist for Templates

**AGENT_GUIDE.md** (Most Important):
- [ ] New CLI commands added → Add to command summary table
- [ ] New API endpoints → Add to API reference section
- [ ] Agent registration process changed → Update registration section
- [ ] New agent roles or capabilities → Update capabilities list

**README.md** (Agent Skills):
- [ ] New workflows → Add to Quick Reference table
- [ ] New skills → Add to Skills Reference section

**Template Workflows**:
- [ ] `implement-issue.md` → Update if issue process changes
- [ ] `test-code.md` → Update if testing procedures change
- [ ] `commit-push.md` → Update if commit format changes

### 3. Template Documentation Integration

The templates should reference the main documentation for completeness:
```markdown
## See Also
- [Full Documentation](../docs/ONBOARDING.md) - Complete onboarding guide
- [API Reference](../docs/API_REFERENCE.md) - Full API endpoints
- [Implementation Guide](../docs/IMPLEMENTATION_GUIDE.md) - Extending the graph
```

### 4. Verify Templates Work

After updating templates, verify they work correctly:
```bash
# Test tasker init in a clean directory
cd /tmp && rm -rf test-project && mkdir test-project && cd test-project
tasker init .
ls -la .agent/  # Verify templates were installed
```

---

## Phase 5: Web Documentation (GitHub Pages)

### 1. Synchronize Web Content
- **Location**: `docs/`
- **Action**: Update the HTML pages to reflect the changes made in Phase 1 & 2.
- **Mandatory Skill**: You MUST follow the rules in `skills/web-docs-management.md`.
- **Constraint**: DO NOT modify the design (CSS/JS) or the site structure. Focus only on the content within the sections.

### 2. Update Sidebars
- If new pages were added, update the sidebar in ALL files under `docs/pages/`.

---

## Phase 6: Verification & Commit

### 1. Link & Format Check
- **Action**:
    - Verify that markdown links between files are not broken.
    - Ensure all code blocks in documentation are valid and follow the current API.

### 2. Documentation-Sync Commit
- **Rule**: Documentation updates should be part of the same commit as the code changes.
- **Commit Message**:
    ```bash
git add src/ .agent/ *.md
git commit -m "docs: sync documentation with v1.0.0 changes

- Updated project.md with new Agent Integration architecture
- Updated README with agent registration commands
- Updated AGENT_GUIDE.md with new CLI commands
- Updated agent workflows for v1.0.0 compliance
- Updated tasker init templates"
    ```

## Checklist

- [ ] Docstrings updated in `src/`
- [ ] `project.md` reflects current architecture
- [ ] `README.md` and `API_REFERENCE.md` updated with new interfaces
- [ ] `ROADMAP.md` and `VERSIONS.md` updated with resolved issues
- [ ] `.agent/` skills and workflows are consistent with current version
- [ ] Distribution assets in `src/.../assets/` are updated
- [ ] **Tasker init templates updated** (see Phase 4b):
  - [ ] `AGENT_GUIDE.md` - New commands and API endpoints
  - [ ] `README.md` - New workflows and skills
  - [ ] `workflows/*.md` - Process changes
  - [ ] `policies.md` - New governance policies
  - [ ] Templates reference main docs correctly
- [ ] **Web documentation in `docs/` is synchronized and follows `web-docs-management.md`**
- [ ] No Spanish text remains in documentation
- [ ] All version references match the current release (v1.0.0)

---

## Audio Notification

When workflow completes, execute:

```bash
.venv/Scripts/python.exe .agent/assets/play_audio.py ".agent/assets/audios/Documentacion actualizada.mp3"
```
