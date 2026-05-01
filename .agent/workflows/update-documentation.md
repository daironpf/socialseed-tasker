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
    git commit -m "docs: sync documentation with v0.9.0 changes
    
    - Updated project.md with new Agent Integration architecture
    - Updated README with reasoning log commands
    - Updated docstrings in core/task_management
    - Updated agent workflows for 0.9.0 compliance"
    ```

## Checklist

- [ ] Docstrings updated in `src/`
- [ ] `project.md` reflects current architecture
- [ ] `README.md` and `API_REFERENCE.md` updated with new interfaces
- [ ] `ROADMAP.md` and `VERSIONS.md` updated with resolved issues
- [ ] `.agent/` skills and workflows are consistent with current version
- [ ] Distribution assets in `src/.../assets/` are updated
- [ ] **Web documentation in `docs/` is synchronized and follows `web-docs-management.md`**
- [ ] No Spanish text remains in documentation
- [ ] All version references match the current release (v0.9.0)
