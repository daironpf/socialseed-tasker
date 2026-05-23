# Release Process and Semantic Versioning

## Purpose
Describe exact steps to prepare, tag, and publish a release using Semantic Versioning.

## Prerequisites
- You have push access to the repository.
- `git` and `gh` (GitHub CLI) are installed and authenticated, or CI has GITHUB_TOKEN.
- Tests pass locally: `pytest -q`.
- Pre-commit hooks run clean: `pre-commit run --all-files`.

## Versioning rules
- Bump MAJOR for incompatible API changes.
- Bump MINOR for added functionality in a backwards-compatible manner.
- Bump PATCH for backwards-compatible bug fixes.

## Step by step local release (deterministic)
1. Ensure working tree is clean:
   ```
   git status --porcelain
   ```
   Abort if any changes exist.

2. Update `CHANGELOG.md` Unreleased section with bullet points describing changes.

3. Run tests and checks:
   ```
   python -m pip install -e ".[dev]"
   pre-commit run --all-files
   ruff check src/
   mypy src/
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

## CI-driven release
- Use `.github/workflows/release.yml` to run tests and create a release when a tag `vX.Y.Z` is pushed or via workflow_dispatch.

## Rollback
- If a release must be reverted, delete the GitHub Release and delete the tag:
  ```
  gh release delete v1.1.0
  git push origin :refs/tags/v1.1.0
  ```

## Audit
- The `scripts/release.sh` prints executed git commands to stdout for auditability.
