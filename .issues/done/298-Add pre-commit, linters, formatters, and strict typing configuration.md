### Issue 298 — Add pre-commit, linters, formatters, and strict typing configuration

**Short description**  
Add deterministic developer tooling and enforcement so every commit and CI run uses the same formatting, linting, and type-checking rules. Implement **pre-commit hooks**, configure **ruff**, **black**, **isort**, and **mypy**, and provide configuration files and a developer onboarding section. The goal is to remove ambiguity for autonomous agents and contributors: code style, import ordering, and typing rules are enforced automatically and consistently.

---

#### Objective (what the agent must deliver)
1. Add pre-commit configuration that runs `ruff`, `black`, `isort`, and `mypy` checks (and auto-fixes where appropriate) on staged files.  
2. Add configuration files for each tool with strict, deterministic settings:
   - `pyproject.toml` (or update existing) with `tool.black`, `tool.isort`, `tool.ruff`, and `tool.mypy` sections.
   - `.pre-commit-config.yaml` with hooks and pinned versions.
   - `mypy.ini` or `pyproject.toml` mypy section with strict rules for `tasker` and relaxed for tests.
3. Add a developer guide `CONTRIBUTING_TOOLING.md` describing how to install pre-commit and run checks locally, and how to fix common failures.
4. Add a GitHub Actions job reference in `.github/workflows/ci.yml` (if present) to run `pre-commit` as a check step in the `lint` job.
5. Create branch `ci/add-precommit-linters` and open a PR with the exact PR body provided below.

---

#### Files to add or modify (exact paths)
- `.pre-commit-config.yaml` **(new)**  
- `pyproject.toml` **(create or update)** — must include `tool.black`, `tool.isort`, `tool.ruff`, and `tool.mypy` sections exactly as specified below.  
- `mypy.ini` **(new)** — strict config for application code, relaxed for tests.  
- `CONTRIBUTING_TOOLING.md` **(new)** — developer instructions.  
- Update `.github/workflows/ci.yml` **(modify)** to include a `Run pre-commit` step in the `lint` job if the workflow exists.

---

#### Exact file contents to add

**`.pre-commit-config.yaml`**
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.10.0
    hooks:
      - id: black
        name: black
        language_version: python3.11
        additional_dependencies: []
        args: ["--line-length=88"]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        name: isort
        language_version: python3.11
        args: ["--profile", "black"]

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        name: ruff
        language_version: python3.11
        args: ["check", "--fix"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.9.5
    hooks:
      - id: mypy
        name: mypy
        language_version: python3.11
        args: ["--config-file", "mypy.ini"]
```

**`pyproject.toml`** (add or merge into existing; include exactly these sections)
```toml
[tool.black]
line-length = 88
target-version = ["py310", "py311", "py312"]
skip-string-normalization = false

[tool.isort]
profile = "black"
line_length = 88
known_first_party = ["tasker"]
known_third_party = ["neo4j", "tree_sitter", "pytest"]
multi_line_output = 3
include_trailing_comma = true

[tool.ruff]
line-length = 88
select = ["E", "F", "W", "C", "B", "I", "TIDY"]
ignore = ["E203"]
extend-ignore = ["W503"]
target-version = "py310"
exclude = ["tests/integration", ".venv", "venv", "build", "dist"]

[tool.mypy]
python_version = "3.11"
warn_unused_configs = true
plugins = []
```

**`mypy.ini`**
```ini
[mypy]
python_version = 3.11
ignore_missing_imports = True
strict = True
warn_unused_ignores = True
warn_return_any = True
warn_unused_configs = True
show_error_codes = True

[mypy-tests.*]
# Tests may use dynamic fixtures and mocks; relax strictness for tests
ignore_errors = True
```

**`CONTRIBUTING_TOOLING.md`**
```markdown
Developer Tooling and Pre-commit Hooks

This project enforces formatting, linting, and typing checks via pre-commit hooks and CI.

Install pre-commit and tooling locally:
1. Install Python 3.11 or compatible.
2. Create a virtual environment and activate it:
   python -m venv .venv
   source .venv/bin/activate
3. Install pre-commit:
   python -m pip install --upgrade pip
   pip install pre-commit

Install hooks:
   pre-commit install
   pre-commit autoupdate

Run checks locally:
- Run all hooks against all files:
  pre-commit run --all-files

- Run black only:
  pre-commit run black --all-files

- Run ruff with auto-fix:
  pre-commit run ruff --all-files

- Run mypy:
  mypy tasker --strict

Common fixes:
- Formatting: run `black .` or `pre-commit run black --all-files`
- Import order: run `isort .` or `pre-commit run isort --all-files`
- Lint fixes: run `pre-commit run ruff --all-files` (ruff will auto-fix many issues)

CI integration:
- The CI workflow runs the same checks. Ensure your branch passes `pre-commit run --all-files` before opening a PR.
```

**`.github/workflows/ci.yml`** — **modification**: add the following step under the `lint` job `steps` after `Install deps` (exact snippet to insert)
```yaml
      - name: Run pre-commit hooks
        run: |
          python -m pip install --upgrade pip
          pip install pre-commit
          pre-commit run --all-files
```

---

#### Exact commands the agent must run
```bash
git checkout -b ci/add-precommit-linters
# create files with exact content above
python -m pip install -e .
pip install pre-commit black isort ruff mypy
pre-commit install
pre-commit run --all-files
# run type checks and linters
black --check .
isort --check-only .
ruff check .
mypy tasker --strict || true
# commit and push
git add .pre-commit-config.yaml pyproject.toml mypy.ini CONTRIBUTING_TOOLING.md
git commit -m "chore(ci): add pre-commit hooks, ruff, black, isort, and mypy configuration"
git push origin ci/add-precommit-linters
```

---

#### PR body exact text to paste
```
Summary:
- Added .pre-commit-config.yaml to run black, isort, ruff, and mypy as pre-commit hooks.
- Added pyproject.toml sections for black, isort, ruff, and mypy configuration.
- Added mypy.ini with strict settings for application code and relaxed settings for tests.
- Added CONTRIBUTING_TOOLING.md with developer instructions.
- Updated .github/workflows/ci.yml lint job to run pre-commit hooks.

Verification steps executed by this agent:
1. Installed pre-commit and tooling locally.
2. Installed hooks: pre-commit install.
3. Ran pre-commit run --all-files (fixed or reported issues).
4. Ran black, isort, ruff, and mypy checks locally.

Files changed:
- .pre-commit-config.yaml
- pyproject.toml
- mypy.ini
- CONTRIBUTING_TOOLING.md
- .github/workflows/ci.yml (lint job updated)

Notes:
- pre-commit hooks are pinned to specific revisions to ensure reproducible behavior.
- Developers should run `pre-commit run --all-files` before opening PRs to avoid CI failures.
```

---

#### Acceptance criteria (must be satisfied exactly)
- `.pre-commit-config.yaml` exists and matches the content above.  
- `pyproject.toml` contains the `tool.black`, `tool.isort`, `tool.ruff`, and `tool.mypy` sections exactly as specified.  
- `mypy.ini` exists and matches the content above.  
- `CONTRIBUTING_TOOLING.md` exists and contains the developer instructions above.  
- `.github/workflows/ci.yml` includes the `Run pre-commit hooks` step in the `lint` job.  
- Running `pre-commit run --all-files` completes (auto-fixes or reports issues) and `black --check .`, `isort --check-only .`, `ruff check .`, and `mypy tasker --strict` run without unexpected configuration errors.  
- Branch `ci/add-precommit-linters` created and PR opened with the exact PR body above.

---

#### Labels to apply on GitHub
- `ci`  
- `tooling`  
- `quality`  
- `small-priority`

---

#### Estimated effort
**Small (S)** — expected to take an autonomous agent or engineer **0.5–2 hours**.