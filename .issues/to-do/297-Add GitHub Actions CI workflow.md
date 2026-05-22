### Issue 297 — Add GitHub Actions CI workflow (lint, typecheck, unit tests, integration jobs)

**Short description**  
Add a deterministic, reproducible GitHub Actions CI pipeline that runs on every push and PR. The workflow must run linters, type checks, unit tests, and optional integration tests (Neo4j + Tree‑Sitter) in separate jobs. The YAML must be explicit about Python versions, caching, environment variables, service containers, and exact commands to run so an autonomous agent can reproduce CI behavior without guessing.

---

#### Objective (what the agent must deliver)
1. Add a GitHub Actions workflow file at `.github/workflows/ci.yml` with the exact content provided below.
2. The workflow must include these jobs:
   - **lint**: run `ruff`, `black --check`, `isort --check-only`.
   - **typecheck**: run `mypy --strict` on `tasker` and `tests`.
   - **unit-tests**: run `pytest` for all unit tests (exclude integration-marked tests).
   - **integration-tests**: optional job that runs only when the workflow is triggered with `integration: true` input or when `TASKER_INTEGRATION=1` is set in the workflow dispatch; it must start Neo4j service via Docker container and run integration tests marked `integration`.
3. Use a matrix for Python versions: `3.10`, `3.11`, `3.12`.
4. Cache pip and poetry/virtualenv artifacts to speed up runs.
5. Provide explicit environment variables and secrets usage (read from repository secrets if present) with sensible defaults for local CI reproducibility.
6. Add a status badge snippet to `README.md` under a new **CI** section (exact markdown provided).
7. Create branch `ci/add-github-actions` and open a PR with the exact PR body provided below.

---

#### Why this must be done exactly this way
- Autonomous agents and contributors must be able to rely on CI to validate changes deterministically.
- Separating lint/typecheck/unit/integration reduces flakiness and makes failures actionable.
- Explicit service definitions and env vars avoid guessing runtime requirements.

---

#### Exact workflow file to add

Create `.github/workflows/ci.yml` with the exact content below. Do not change job or step names.

```yaml
name: CI

on:
  push:
    branches: [ main, master, develop ]
  pull_request:
    branches: [ main, master, develop ]
  workflow_dispatch:
    inputs:
      integration:
        description: 'Run integration tests (true/false)'
        required: false
        default: 'false'

env:
  PYTHON_VERSIONS: "3.10,3.11,3.12"
  PIP_CACHE_DIR: ${{ runner.temp }}/pip-cache

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.10, 3.11, 3.12]
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ${{ env.PIP_CACHE_DIR }}
          key: ${{ runner.os }}-pip-${{ matrix.python-version }}-${{ hashFiles('**/pyproject.toml') }}
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install ruff black isort
      - name: Run ruff
        run: ruff check .
      - name: Run black check
        run: black --check .
      - name: Run isort check
        run: isort --check-only .

  typecheck:
    name: Typecheck
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.10, 3.11, 3.12]
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ${{ env.PIP_CACHE_DIR }}
          key: ${{ runner.os }}-pip-${{ matrix.python-version }}-${{ hashFiles('**/pyproject.toml') }}
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install mypy
          pip install -e .
      - name: Run mypy
        run: mypy tasker --strict

  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.10, 3.11, 3.12]
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ${{ env.PIP_CACHE_DIR }}
          key: ${{ runner.os }}-pip-${{ matrix.python-version }}-${{ hashFiles('**/pyproject.toml') }}
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install -e .
          pip install pytest pytest-cov
      - name: Run unit tests
        run: |
          pytest -q -k "not integration" --maxfail=1 --disable-warnings

  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    if: ${{ github.event.inputs.integration == 'true' || env.TASKER_INTEGRATION == '1' }}
    services:
      neo4j:
        image: neo4j:5.11
        env:
          NEO4J_AUTH: "neo4j/test"
        ports:
          - 7474:7474
          - 7687:7687
        options: >-
          --health-cmd "cypher-shell -u neo4j -p test 'RETURN 1' || exit 1"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 12
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11
      - name: Wait for Neo4j
        run: |
          echo "Waiting for Neo4j to be healthy..."
          for i in $(seq 1 60); do
            if docker run --rm --network host curlimages/curl:8.2.1 -sSf http://localhost:7474/ >/dev/null 2>&1; then
              echo "Neo4j HTTP reachable"
              break
            fi
            sleep 1
          done
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install -e .
          pip install pytest pytest-cov
      - name: Run integration tests
        env:
          TASKER_NEO4J_URI: "bolt://localhost:7687"
          TASKER_NEO4J_USER: "neo4j"
          TASKER_NEO4J_PASSWORD: "test"
          TASKER_INTEGRATION: "1"
        run: |
          pytest -q -m integration --maxfail=1 --disable-warnings
```

---

#### Exact README badge to add

Add the following under a new **CI** section in `README.md` (append at top-level). Insert the exact markdown snippet below.

```markdown
## CI

![CI](https://github.com/<OWNER>/<REPO>/actions/workflows/ci.yml/badge.svg)
```

Replace `<OWNER>` and `<REPO>` with the repository owner and name before merging.

---

#### Commands the agent must run exactly

```bash
git checkout -b ci/add-github-actions
# create workflow file
mkdir -p .github/workflows
# write .github/workflows/ci.yml with the exact content above
# update README.md to include CI badge snippet
git add .github/workflows/ci.yml README.md
git commit -m "ci: add GitHub Actions workflow for lint, typecheck, unit and optional integration tests"
git push origin ci/add-github-actions
```

---

#### PR body exact text to paste

```
Summary:
- Added GitHub Actions workflow .github/workflows/ci.yml that runs lint, typecheck, unit tests, and optional integration tests.
- Integration job starts a Neo4j service and runs tests marked with @pytest.mark.integration when triggered.
- Added CI badge snippet to README.md (replace <OWNER>/<REPO> before merging).

Verification steps executed by this agent:
1. Created branch ci/add-github-actions.
2. Added workflow file and README badge snippet.
3. Workflow is configured to run on push and PR; integration tests run only when explicitly requested.

Files changed:
- .github/workflows/ci.yml
- README.md

Notes:
- To run integration tests in CI, trigger workflow_dispatch with input integration=true or set TASKER_INTEGRATION=1 in the workflow environment.
- The workflow uses Neo4j image neo4j:5.11 with credentials neo4j/test for integration tests.
```

---

#### Acceptance criteria (must be satisfied exactly)
- `.github/workflows/ci.yml` exists and matches the YAML content above.
- `README.md` contains the CI badge snippet under a **CI** section.
- Workflow uses Python matrix `3.10, 3.11, 3.12`.
- Integration job runs only when `integration` input is `true` or `TASKER_INTEGRATION=1`.
- Branch `ci/add-github-actions` created and PR opened with the exact PR body above.

---

#### Labels to apply on GitHub
- `ci`
- `infra`
- `automation`
- `medium-priority`

---

#### Estimated effort
**Small (S)** — expected to take an autonomous agent or engineer **0.5–2 hours** to add and validate.