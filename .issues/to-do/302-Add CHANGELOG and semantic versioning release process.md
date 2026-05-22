### Issue 302 — Add CHANGELOG and semantic versioning release process

**Short description**  
Create a deterministic, machine‑friendly release process using **Semantic Versioning** and a maintained `CHANGELOG.md`. Provide release templates, a release checklist, and automation guidance so an autonomous agent can create, validate, and publish releases without guessing steps or formats.

---

#### Objective (what the agent must deliver)
1. Add `CHANGELOG.md` following the Keep a Changelog format with an initial **Unreleased** section and a documented release history entry for `v1.0.0` (seed content).  
2. Add `RELEASE_PROCESS.md` describing exact steps to prepare, tag, and publish a release using semantic versioning (`MAJOR.MINOR.PATCH`) and the `CHANGELOG.md`. Include exact git commands, branch rules, and verification steps.  
3. Add `release` helper script `scripts/release.sh` that:
   - Validates `CHANGELOG.md` has an Unreleased section with content.
   - Accepts a single argument: new version (e.g., `1.1.0`).
   - Updates `CHANGELOG.md` by moving Unreleased content under a new heading `## [vX.Y.Z] - YYYY-MM-DD`.
   - Commits the change, creates a signed annotated tag `vX.Y.Z`, and pushes tag and branch to origin.
   - Prints exact commands it executed to stdout for auditability.
   - Exits nonzero on any validation failure.
4. Add `RELEASE_TEMPLATE.md` to be used as the GitHub Release body. The template must include: summary, highlights, migration notes, breaking changes, and verification checklist.  
5. Add a GitHub Actions workflow `release.yml` that can be triggered manually (`workflow_dispatch`) and will:
   - Validate the tag format `v\d+\.\d+\.\d+`.
   - Build the package (install and run tests).
   - Create a GitHub Release using the `CHANGELOG.md` entry for the tag (requires `GITHUB_TOKEN`).
   - Upload built artifacts (wheel and sdist) to the release.
6. Add a `RELEASE_CHECKLIST.md` with exact verification steps to run locally or in CI before publishing.  
7. Create branch `release/add-changelog-process` and open a PR with the exact PR body provided below.

---

#### Why this must be done exactly this way
- Autonomous agents and contributors must follow a single, unambiguous release process to avoid inconsistent versioning, missing changelog entries, or broken releases.  
- The `scripts/release.sh` enforces deterministic edits and commands so agents can run releases programmatically and audit the actions taken.

---

#### Files to add or modify (exact paths)
- `CHANGELOG.md` **(new)**  
- `RELEASE_PROCESS.md` **(new)**  
- `scripts/release.sh` **(new, executable)**  
- `RELEASE_TEMPLATE.md` **(new)**  
- `.github/workflows/release.yml` **(new)**  
- `RELEASE_CHECKLIST.md` **(new)**

---

#### Exact content to add

**`CHANGELOG.md`**
```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project adheres to Semantic Versioning.

## [Unreleased]

- Initial changelog entry placeholder. Add bullet points describing changes for the next release.

## [v1.0.0] - 2026-05-21

### Added
- Initial public release with core features: modular architecture, Neo4j adapter, parser adapter, CLI, repositories, use cases, tests, CI, and examples.

### Changed
- N/A

### Fixed
- N/A
```

---

**`RELEASE_PROCESS.md`**
```markdown
Release Process and Semantic Versioning

Purpose
- Describe exact steps to prepare, tag, and publish a release using Semantic Versioning.

Prerequisites
- You have push access to the repository.
- `git` and `gh` (GitHub CLI) are installed and authenticated, or CI has GITHUB_TOKEN.
- Tests pass locally: `pytest -q`.
- Pre-commit hooks run clean: `pre-commit run --all-files`.

Versioning rules
- Bump MAJOR for incompatible API changes.
- Bump MINOR for added functionality in a backwards-compatible manner.
- Bump PATCH for backwards-compatible bug fixes.

Step by step local release (deterministic)
1. Ensure working tree is clean:
   ```
   git status --porcelain
   ```
   Abort if any changes exist.

2. Update `CHANGELOG.md` Unreleased section with bullet points describing changes.

3. Run tests and checks:
   ```
   python -m pip install -e .
   pre-commit run --all-files
   ruff check .
   mypy tasker --strict
   pytest -q
   ```

4. Choose new version (example `1.1.0`) and run the release script:
   ```
   ./scripts/release.sh 1.1.0
   ```
   The script will:
   - Validate `CHANGELOG.md` Unreleased has content.
   - Move Unreleased content under `## [v1.1.0] - YYYY-MM-DD`.
   - Commit the changelog update.
   - Create an annotated signed tag `v1.1.0`.
   - Push branch and tag to `origin`.

5. Create GitHub Release (manual or via `gh`):
   - Manual: open the release page and paste the `RELEASE_TEMPLATE.md` content, then copy the changelog section for `v1.1.0` into the release body.
   - Using GitHub CLI:
     ```
     gh release create v1.1.0 --title "v1.1.0" --notes-file RELEASE_TEMPLATE.md
     ```

6. Verify release artifacts:
   - Ensure wheels and sdist are attached if CI builds them.
   - Confirm release notes include changelog entries.

CI-driven release
- Use `.github/workflows/release.yml` to run tests and create a release when a tag `vX.Y.Z` is pushed or via workflow_dispatch.

Rollback
- If a release must be reverted, delete the GitHub Release and delete the tag:
  ```
  gh release delete v1.1.0
  git push origin :refs/tags/v1.1.0
  ```

Audit
- The `scripts/release.sh` prints executed git commands to stdout for auditability.
```

---

**`scripts/release.sh`** (make executable)
```bash
#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <new-version>  e.g. $0 1.1.0" >&2
  exit 2
fi

NEW_VERSION="$1"
TAG="v${NEW_VERSION}"
DATE="$(date -u +%F)"

# Validate version format
if ! [[ "${NEW_VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Version must be semantic version X.Y.Z" >&2
  exit 3
fi

# Ensure clean working tree
if [ -n "$(git status --porcelain)" ]; then
  echo "Working tree is not clean. Commit or stash changes before releasing." >&2
  git status --porcelain
  exit 4
fi

# Ensure Unreleased section exists and has content
if ! grep -q "^## \\[Unreleased\\]" CHANGELOG.md; then
  echo "CHANGELOG.md missing Unreleased section" >&2
  exit 5
fi

# Extract Unreleased content
UNRELEASED_CONTENT="$(awk '/^## \\[Unreleased\\]/ {flag=1; next} /^## \\[v[0-9]+\\.[0-9]+\\.[0-9]+\\]/ {flag=0} flag {print}' CHANGELOG.md || true)"
if [ -z "${UNRELEASED_CONTENT// /}" ]; then
  echo "Unreleased section is empty. Add changelog entries before releasing." >&2
  exit 6
fi

# Prepare new changelog entry
TMPFILE="$(mktemp)"
awk -v ver="${NEW_VERSION}" -v date="${DATE}" '
  BEGIN {printed=0}
  /^## \\[Unreleased\\]/ {
    print "## [Unreleased]\n"
    # skip lines until next version header
    next
  }
  { print }
' CHANGELOG.md > "${TMPFILE}.base"

# Build new changelog: replace Unreleased with Unreleased header and insert new version after it
{
  awk '1; /^## \\[Unreleased\\]/ { exit }' CHANGELOG.md
  echo ""
  echo "## [v${NEW_VERSION}] - ${DATE}"
  echo ""
  echo "${UNRELEASED_CONTENT}"
  echo ""
  # append the rest of the file after Unreleased section
  awk 'BEGIN{skip=0} /^## \\[Unreleased\\]/{skip=1; next} /^## \\[v[0-9]+\\.[0-9]+\\.[0-9]+\\]/{skip=0} { if(skip==0) print }' CHANGELOG.md | sed '1,1d'
} > CHANGELOG.md.new

mv CHANGELOG.md.new CHANGELOG.md

# Commit and tag
git add CHANGELOG.md
git commit -m "chore(release): prepare v${NEW_VERSION} [skip ci]"
echo "git commit -m \"chore(release): prepare v${NEW_VERSION} [skip ci]\""
git tag -s "${TAG}" -m "Release ${TAG}"
echo "git tag -s ${TAG} -m \"Release ${TAG}\""
git push origin HEAD
echo "git push origin HEAD"
git push origin "${TAG}"
echo "git push origin ${TAG}"

echo "Release ${TAG} created and pushed. Next: create GitHub Release using CHANGELOG entry."
```

---

**`RELEASE_TEMPLATE.md`**
```markdown
Release Title
- Version: vX.Y.Z
- Date: YYYY-MM-DD

Summary
- Short summary of the release in one or two sentences.

Highlights
- Bullet list of the most important changes.

Migration Notes
- Any steps users must take to upgrade safely.

Breaking Changes
- List breaking changes with clear migration guidance.

Verification Checklist
- [ ] Tests passed locally and in CI
- [ ] CHANGELOG updated and committed
- [ ] Tag pushed to origin
- [ ] Release created on GitHub with artifacts attached
- [ ] Smoke test performed on a fresh environment
```

---

**`.github/workflows/release.yml`**
```yaml
name: Release

on:
  workflow_dispatch:
  push:
    tags:
      - 'v*.*.*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11

      - name: Validate tag format
        if: startsWith(github.ref, 'refs/tags/v')
        run: |
          TAG="${GITHUB_REF#refs/tags/}"
          if ! [[ "${TAG}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "Tag ${TAG} does not match vX.Y.Z" >&2
            exit 1
          fi
          echo "Tag ${TAG} validated"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .
          pip install pytest

      - name: Run tests
        run: pytest -q

      - name: Extract changelog entry
        id: changelog
        run: |
          TAG="${GITHUB_REF#refs/tags/}"
          VERSION="${TAG#v}"
          awk -v ver="v${VERSION}" '
            $0 == "## [Unreleased]" {found=1; next}
            found && $0 ~ "^## \\[v[0-9]+\\.[0-9]+\\.[0-9]+\\]" {exit}
            found {print}
          ' CHANGELOG.md > /tmp/release_notes.txt
          echo "::set-output name=notes::$(sed ':a;N;$!ba;s/\n/\\n/g' /tmp/release_notes.txt)"

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          tag_name: ${{ github.ref_name }}
          name: ${{ github.ref_name }}
          body: ${{ steps.changelog.outputs.notes }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Build artifacts
        run: |
          python -m pip install build
          python -m build

      - name: Upload release assets
        uses: softprops/action-gh-release@v1
        with:
          tag_name: ${{ github.ref_name }}
          files: "dist/*"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

**`RELEASE_CHECKLIST.md`**
```markdown
Release Checklist

Before running ./scripts/release.sh:
- [ ] Working tree is clean
- [ ] CHANGELOG.md Unreleased section updated with bullet points
- [ ] All tests pass: pytest -q
- [ ] Pre-commit hooks pass: pre-commit run --all-files
- [ ] Lint and type checks pass: ruff check .; mypy tasker --strict

After running ./scripts/release.sh <version>:
- [ ] Tag pushed to origin
- [ ] GitHub Release created with changelog notes
- [ ] Artifacts attached to release (wheel and sdist)
- [ ] Smoke test performed: install package from release and run basic commands
```

---

#### Commands the agent must run exactly
```bash
git checkout -b release/add-changelog-process
# create files as specified
chmod +x scripts/release.sh
git add CHANGELOG.md RELEASE_PROCESS.md scripts/release.sh RELEASE_TEMPLATE.md .github/workflows/release.yml RELEASE_CHECKLIST.md
git commit -m "chore(release): add CHANGELOG and deterministic release process with automation"
git push origin release/add-changelog-process
```

---

#### PR body exact text to paste
```
Summary:
- Added CHANGELOG.md following Keep a Changelog with an Unreleased section and v1.0.0 seed.
- Added RELEASE_PROCESS.md documenting exact semantic versioning and release steps.
- Added scripts/release.sh to validate and perform changelog update, commit, tag, and push.
- Added RELEASE_TEMPLATE.md for GitHub Release body.
- Added .github/workflows/release.yml to validate tags, run tests, and create GitHub Releases with artifacts.
- Added RELEASE_CHECKLIST.md with verification steps.

Verification steps executed by this agent:
1. Created branch release/add-changelog-process.
2. Added changelog and release automation scripts.
3. Ensured release script is executable and prints executed git commands for audit.
4. Provided CI workflow to create releases from tags.

Files changed:
- CHANGELOG.md
- RELEASE_PROCESS.md
- scripts/release.sh
- RELEASE_TEMPLATE.md
- .github/workflows/release.yml
- RELEASE_CHECKLIST.md

Notes:
- The release workflow requires GITHUB_TOKEN for creating releases and uploading artifacts.
- The release script enforces that Unreleased section is non-empty before creating a release.
```

---

#### Acceptance criteria (must be satisfied exactly)
- `CHANGELOG.md` exists and contains an **Unreleased** section and a `v1.0.0` entry as shown.  
- `RELEASE_PROCESS.md` exists and documents the exact step-by-step release process.  
- `scripts/release.sh` exists, is executable, accepts a single version argument, validates `CHANGELOG.md` Unreleased content, updates the changelog, commits, tags, and pushes, and prints executed git commands.  
- `RELEASE_TEMPLATE.md` exists and matches the template above.  
- `.github/workflows/release.yml` exists and validates tag format, runs tests, extracts changelog notes, creates a GitHub Release, builds artifacts, and uploads them.  
- `RELEASE_CHECKLIST.md` exists and lists the verification steps.  
- Branch `release/add-changelog-process` created and PR opened with the exact PR body above.

---

#### Labels to apply on GitHub
- `release`
- `automation`
- `infra`
- `medium-priority`

---

#### Estimated effort
**Small (S)** — expected to take an autonomous agent or engineer **0.5–2 hours**.