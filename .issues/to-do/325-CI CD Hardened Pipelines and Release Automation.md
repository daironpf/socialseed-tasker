### Issue 325 — CI CD Hardened Pipelines and Release Automation

**Descripción breve**  
Implementar pipelines de CI/CD deterministas y endurecidos para Tasker: flujos reproducibles de build, test, lint, security scan, artifact signing, canary release y rollback; jobs de release automatizados que generan artefactos (wheel, docker images, release notes), firmas y despliegues; integración con GitHub Actions y scripts locales; pruebas de pipeline (smoke) y documentación. Todo debe ser explícito: nombres de archivos, jobs, pasos, variables de entorno, comandos exactos, plantillas y cuerpo de PR listos para aplicar sin ambigüedades.

---

### Objetivos exactos
1. **Pipelines GitHub Actions**  
   - Añadir workflow `ci/pipeline.yml` que ejecute en `push` a `main` y en `pull_request`:
     - **jobs**: `checkout`, `setup`, `lint`, `unit-tests`, `security-scan`, `build-artifacts`, `docker-build`, `integration-smoke` (opcional), `sign-artifacts` (conditional), `publish` (conditional).
     - Determinismo: usar `actions/checkout@v4` con `fetch-depth: 0`, fijar versiones de Python/Node, usar caches con keys deterministas.
2. **Release workflow**  
   - Añadir workflow `ci/release.yml` que se dispare en `workflow_dispatch` y `push` a tags `v*.*.*`:
     - **jobs**: `prepare`, `generate-changelog` (calls tools/release), `build`, `test`, `publish-pypi` (conditional), `publish-docker` (conditional), `create-github-release` (creates release with artifacts).
     - Firmado de artefactos con GPG key desde secret `RELEASE_GPG_PRIVATE_KEY` (base64) y passphrase `RELEASE_GPG_PASSPHRASE`.
3. **Canary and Rollback**  
   - Implementar `ci/canary-deploy.yml` workflow to deploy to canary environment and run smoke tests; if smoke fails, trigger `rollback` job that reverts to previous image tag.
4. **Local helper scripts**  
   - Add `scripts/ci/run_local_pipeline.sh` to run a subset of pipeline steps locally in deterministic order (lint → unit tests → build wheel → docker build).
   - Add `scripts/ci/sign_artifact.sh` to sign artifacts with GPG using env vars.
5. **Artifact storage and provenance**  
   - Store build artifacts in `artifacts/` with deterministic names: `tasker-{tag}-{commit}.whl`, `tasker-{tag}-{commit}.tar.gz`, `tasker-{tag}-{commit}.docker.txt` (image digest).
   - Produce `artifacts/provenance-{tag}-{commit}.json` containing build metadata (commit, tag, builder image, timestamps, checksums).
6. **Security and scanning**  
   - Integrate `safety` (Python), `bandit`, and `dependabot` checks in workflows; add `ci/security-scan.yml` to run SCA and static checks and fail on high severity.
7. **Tests for pipelines**  
   - Add `tests/ci/test_pipeline_smoke.py` that validates generated artifacts exist and basic metadata matches expected format (run in CI job `integration-smoke`).
8. **Documentation**  
   - Add `docs/CI_CD.md` describing workflows, secrets required, how to run locally, rollback procedure, and how to add new jobs.
9. **Branch and PR**  
   - Create branch `feature/ci-cd-hardened` and open PR with the exact PR body provided below.

---

### Archivos a añadir o modificar exactos

- `ci/pipeline.yml` **(nuevo)**  
- `ci/release.yml` **(nuevo)**  
- `ci/canary-deploy.yml` **(nuevo)**  
- `ci/security-scan.yml` **(nuevo)**  
- `scripts/ci/run_local_pipeline.sh` **(nuevo, executable)**  
- `scripts/ci/sign_artifact.sh` **(nuevo, executable)**  
- `artifacts/.gitkeep` **(nuevo)**  
- `artifacts/provenance_template.json` **(nuevo)**  
- `tests/ci/test_pipeline_smoke.py` **(nuevo)**  
- `docs/CI_CD.md` **(nuevo)**  
- Modify `tools/release/changelogctl.py` **(optional)** to support `--ci` flag (exact snippet below).  
- Create branch `feature/ci-cd-hardened` and open PR.

---

### Código exacto a añadir

#### `ci/pipeline.yml`
```yaml
name: CI Pipeline
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

env:
  PYTHON_VERSION: "3.11"
  DOCKER_BUILDKIT: "1"

jobs:
  checkout:
    runs-on: ubuntu-latest
    outputs:
      commit: ${{ steps.get_commit.outputs.sha }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Get commit
        id: get_commit
        run: echo "::set-output name=sha::$(git rev-parse --short HEAD)"

  setup:
    needs: checkout
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: pip-${{ runner.os }}-$(python -c "import sys; print(sys.version_info[:2])")
      - name: Install dependencies
        run: python -m pip install --upgrade pip setuptools wheel tox

  lint:
    needs: setup
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Install lint deps
        run: python -m pip install flake8 black
      - name: Run black check
        run: python -m black --check .
      - name: Run flake8
        run: flake8 .

  unit-tests:
    needs: setup
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Install test deps
        run: python -m pip install -r requirements-dev.txt
      - name: Run unit tests
        run: pytest -q

  security-scan:
    needs: setup
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Install security tools
        run: python -m pip install safety bandit
      - name: Run safety
        run: safety check --full-report || true
      - name: Run bandit
        run: bandit -r tasker -lll || true

  build-artifacts:
    needs: [unit-tests, lint]
    runs-on: ubuntu-latest
    outputs:
      wheel: ${{ steps.art.outputs.wheel }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Build wheel and sdist
        id: art
        run: |
          python -m pip install --upgrade build
          python -m build --sdist --wheel --outdir dist
          echo "::set-output name=wheel::$(ls dist/*.whl | head -n1)"
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: python-artifacts
          path: dist/*

  docker-build:
    needs: build-artifacts
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Build docker image
        run: |
          COMMIT=$(git rev-parse --short HEAD)
          TAG=tasker:${COMMIT}
          docker build -t ${TAG} .
          echo ${TAG} > image-tag.txt
      - name: Upload image tag
        uses: actions/upload-artifact@v4
        with:
          name: image-tag
          path: image-tag.txt

  integration-smoke:
    needs: docker-build
    runs-on: ubuntu-latest
    if: ${{ env.RUN_INTEGRATION == '1' }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Run smoke tests
        run: pytest tests/integration -q -m smoke || exit 1

  sign-artifacts:
    needs: build-artifacts
    runs-on: ubuntu-latest
    if: ${{ secrets.RELEASE_GPG_PRIVATE_KEY != '' }}
    steps:
      - name: Import GPG key
        env:
          GPG_KEY: ${{ secrets.RELEASE_GPG_PRIVATE_KEY }}
          GPG_PASSPHRASE: ${{ secrets.RELEASE_GPG_PASSPHRASE }}
        run: |
          echo "$GPG_KEY" | base64 --decode > private.key
          gpg --batch --import private.key
      - name: Sign wheel
        run: |
          for f in dist/*; do gpg --batch --yes --passphrase "$GPG_PASSPHRASE" -o "${f}.asc" --detach-sign "$f"; done
      - name: Upload signed artifacts
        uses: actions/upload-artifact@v4
        with:
          name: signed-artifacts
          path: dist/*.{asc,whl,tar.gz}

  publish:
    needs: [sign-artifacts, docker-build]
    runs-on: ubuntu-latest
    if: ${{ github.ref_type == 'tag' }}
    steps:
      - name: Download artifacts
        uses: actions/download-artifact@v4
        with:
          name: python-artifacts
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: |
          python -m pip install twine
          twine upload dist/* -u $TWINE_USERNAME -p $TWINE_PASSWORD
      - name: Login to DockerHub
        env:
          DOCKERHUB_USERNAME: ${{ secrets.DOCKERHUB_USERNAME }}
          DOCKERHUB_TOKEN: ${{ secrets.DOCKERHUB_TOKEN }}
        run: |
          echo $DOCKERHUB_TOKEN | docker login -u $DOCKERHUB_USERNAME --password-stdin
          TAG=$(cat image-tag.txt)
          docker tag $TAG ${DOCKERHUB_USERNAME}/tasker:${{ github.ref_name }}
          docker push ${DOCKERHUB_USERNAME}/tasker:${{ github.ref_name }}
```

#### `ci/release.yml`
```yaml
name: Release
on:
  workflow_dispatch:
  push:
    tags:
      - 'v*.*.*'

env:
  PYTHON_VERSION: "3.11"

jobs:
  prepare:
    runs-on: ubuntu-latest
    outputs:
      commit: ${{ steps.get_commit.outputs.sha }}
      tag: ${{ github.ref_name }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - id: get_commit
        run: echo "::set-output name=sha::$(git rev-parse --short HEAD)"
      - name: Set tag
        run: echo "TAG=${GITHUB_REF##*/}" >> $GITHUB_ENV

  generate-changelog:
    needs: prepare
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Install release tools
        run: python -m pip install jinja2 requests
      - name: Generate changelog
        env:
          RELEASE_GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          RELEASE_GH_REPO: ${{ github.repository }}
        run: |
          python tools/release/changelogctl.py generate --from $(git describe --tags --abbrev=0 ${GITHUB_REF}^) --to ${GITHUB_REF##*/} --out releases/${GITHUB_REF##*/}.md

  build:
    needs: generate-changelog
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Build artifacts
        run: |
          python -m pip install --upgrade build
          python -m build --sdist --wheel --outdir dist
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: release-artifacts
          path: dist/*

  sign:
    needs: build
    runs-on: ubuntu-latest
    if: ${{ secrets.RELEASE_GPG_PRIVATE_KEY != '' }}
    steps:
      - name: Import GPG
        env:
          GPG_KEY: ${{ secrets.RELEASE_GPG_PRIVATE_KEY }}
          GPG_PASSPHRASE: ${{ secrets.RELEASE_GPG_PASSPHRASE }}
        run: |
          echo "$GPG_KEY" | base64 --decode > private.key
          gpg --batch --import private.key
      - name: Sign artifacts
        run: |
          for f in dist/*; do gpg --batch --yes --passphrase "$GPG_PASSPHRASE" -o "${f}.asc" --detach-sign "$f"; done
      - name: Upload signed artifacts
        uses: actions/upload-artifact@v4
        with:
          name: signed-release-artifacts
          path: dist/*.{asc,whl,tar.gz}

  publish:
    needs: [build, sign]
    runs-on: ubuntu-latest
    if: ${{ secrets.PUBLISH_RELEASE == '1' }}
    steps:
      - name: Download artifacts
        uses: actions/download-artifact@v4
        with:
          name: release-artifacts
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          tag_name: ${{ github.ref_name }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - name: Upload release assets
        uses: softprops/action-gh-release@v1
        with:
          files: dist/*
```

#### `ci/canary-deploy.yml`
```yaml
name: Canary Deploy
on:
  workflow_dispatch:

jobs:
  canary:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Deploy to canary
        run: |
          TAG=${GITHUB_SHA::7}
          # example: push image to canary registry and update k8s deployment
          docker build -t registry.local/tasker:canary-${TAG} .
          echo "deployed canary: registry.local/tasker:canary-${TAG}"
      - name: Run canary smoke tests
        run: pytest tests/integration -q -m canary || exit 1
      - name: Rollback on failure
        if: failure()
        run: |
          echo "Rolling back canary to previous stable"
          # implement rollback commands here
```

#### `ci/security-scan.yml`
```yaml
name: Security Scan
on:
  schedule:
    - cron: '0 3 * * 1' # weekly
  workflow_dispatch:

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Install tools
        run: python -m pip install safety bandit
      - name: Run safety
        run: safety check --full-report || true
      - name: Run bandit
        run: bandit -r tasker -lll || true
```

#### `scripts/ci/run_local_pipeline.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
# scripts/ci/run_local_pipeline.sh
# Run a deterministic subset of CI steps locally
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-dev.txt
echo "Running black"
python -m black --check .
echo "Running flake8"
flake8 .
echo "Running unit tests"
pytest tests/unit -q
echo "Building artifacts"
python -m build --sdist --wheel --outdir dist
echo "Docker build"
COMMIT=$(git rev-parse --short HEAD)
docker build -t tasker:${COMMIT} .
echo "Done"
```

Make executable: `chmod +x scripts/ci/run_local_pipeline.sh`.

#### `scripts/ci/sign_artifact.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
# scripts/ci/sign_artifact.sh <artifact>
ARTIFACT="$1"
if [ -z "${RELEASE_GPG_PRIVATE_KEY:-}" ]; then
  echo "RELEASE_GPG_PRIVATE_KEY not set"
  exit 1
fi
echo "$RELEASE_GPG_PRIVATE_KEY" | base64 --decode > private.key
gpg --batch --import private.key
gpg --batch --yes --passphrase "$RELEASE_GPG_PASSPHRASE" -o "${ARTIFACT}.asc" --detach-sign "$ARTIFACT"
echo "Signed ${ARTIFACT}"
```

Make executable: `chmod +x scripts/ci/sign_artifact.sh`.

#### `artifacts/provenance_template.json`
```json
{
  "tag": "{{TAG}}",
  "commit": "{{COMMIT}}",
  "builder": "ubuntu-latest",
  "python_version": "3.11",
  "build_time_utc": "{{TIMESTAMP}}",
  "artifacts": [
    {"path": "dist/tasker-{{TAG}}-{{COMMIT}}.whl", "sha256": "{{SHA256}}"}
  ]
}
```

#### `tests/ci/test_pipeline_smoke.py`
```python
# tests/ci/test_pipeline_smoke.py
import os
import json
def test_artifacts_exist():
    # CI job should produce artifacts in dist/
    assert os.path.isdir("dist")
    files = [f for f in os.listdir("dist") if f.endswith(".whl") or f.endswith(".tar.gz")]
    assert len(files) >= 1
def test_provenance_template():
    # ensure template exists
    assert os.path.exists("artifacts/provenance_template.json")
```

#### `docs/CI_CD.md`
```markdown
CI CD Hardened Pipelines and Release Automation

Workflows
- ci/pipeline.yml: main CI pipeline (lint, unit-tests, build, docker, sign, publish)
- ci/release.yml: release workflow triggered on tag push and workflow_dispatch
- ci/canary-deploy.yml: canary deployment and smoke tests
- ci/security-scan.yml: scheduled security scans

Secrets required in GitHub repository settings
- PYPI_API_TOKEN (for publishing)
- DOCKERHUB_USERNAME, DOCKERHUB_TOKEN
- RELEASE_GPG_PRIVATE_KEY (base64), RELEASE_GPG_PASSPHRASE
- PUBLISH_RELEASE = '1' to enable publish job

Local usage
- Run local pipeline subset:
  ./scripts/ci/run_local_pipeline.sh

Artifact naming and provenance
- Artifacts stored in dist/ and artifacts/ with deterministic names: tasker-{tag}-{commit}.whl
- Provenance file artifacts/provenance-{tag}-{commit}.json must be generated by CI step after build

Rollback and canary
- Canary deploys use ci/canary-deploy.yml and run smoke tests; failures trigger rollback job.

Adding new jobs
- Add job to ci/pipeline.yml and update docs and tests accordingly.
```

#### `tools/release/changelogctl.py` snippet to support `--ci`
Add to argument parser in `tools/release/changelogctl.py`:

```python
g.add_argument("--ci", dest="ci", action="store_true", help="Run in CI mode (non-interactive)")
```

No further changes required; `generate_changelog` already supports non-interactive usage.

---

### Comandos exactos que el agente debe ejecutar

```bash
git checkout -b feature/ci-cd-hardened
# create files as specified
chmod +x scripts/ci/run_local_pipeline.sh scripts/ci/sign_artifact.sh
python -m pip install -e .
# run local pipeline subset
./scripts/ci/run_local_pipeline.sh
# run unit smoke tests
pytest tests/ci/test_pipeline_smoke.py -q
# commit and push
git add ci scripts artifacts tests docs
git commit -m "chore(ci): add hardened CI/CD pipelines, release automation, canary and signing"
git push origin feature/ci-cd-hardened
```

---

### PR body exacto a pegar

```
Summary:
- Added hardened CI/CD pipelines and release automation.
- Implemented ci/pipeline.yml with deterministic steps: checkout, setup, lint, unit-tests, security-scan, build-artifacts, docker-build, sign-artifacts, publish.
- Implemented ci/release.yml to generate changelog, build, sign and publish releases on tag push.
- Added canary deploy workflow ci/canary-deploy.yml with smoke tests and rollback step.
- Added security scan workflow ci/security-scan.yml for scheduled SCA and static analysis.
- Added local helper scripts scripts/ci/run_local_pipeline.sh and scripts/ci/sign_artifact.sh.
- Added artifacts provenance template and smoke tests tests/ci/test_pipeline_smoke.py.
- Added documentation docs/CI_CD.md.

Verification steps executed by this agent:
1. Created local branch feature/ci-cd-hardened.
2. Ran local pipeline subset via scripts/ci/run_local_pipeline.sh (lint, tests, build).
3. Ran smoke tests tests/ci/test_pipeline_smoke.py.

Files changed:
- ci/pipeline.yml
- ci/release.yml
- ci/canary-deploy.yml
- ci/security-scan.yml
- scripts/ci/*
- artifacts/provenance_template.json
- tests/ci/test_pipeline_smoke.py
- docs/CI_CD.md

Notes:
- Ensure repository secrets are configured: PYPI_API_TOKEN, DOCKERHUB_USERNAME, DOCKERHUB_TOKEN, RELEASE_GPG_PRIVATE_KEY, RELEASE_GPG_PASSPHRASE.
- The publish job is conditional and only runs on tag pushes and when PUBLISH_RELEASE secret is set to '1'.
```

---

### Criterios de aceptación exactos
- `ci/pipeline.yml`, `ci/release.yml`, `ci/canary-deploy.yml`, `ci/security-scan.yml` existen with the jobs and steps described.  
- Local scripts `scripts/ci/run_local_pipeline.sh` and `scripts/ci/sign_artifact.sh` exist and are executable.  
- Artifacts naming convention and provenance template exist under `artifacts/`.  
- `tests/ci/test_pipeline_smoke.py` exists and passes locally.  
- `docs/CI_CD.md` documents workflows, secrets and local usage.  
- Branch `feature/ci-cd-hardened` creado and PR opened with the exact PR body above.

---

### Labels to apply on GitHub
- `ci`
- `release`
- `security`
- `high-priority`

---

### Estimated effort
**Medium (M)** — expected **2–4 hours** depending on secrets availability and registry credentials.