# Release Checklist

## Before running ./scripts/release.sh:
- [ ] Working tree is clean
- [ ] CHANGELOG.md Unreleased section updated with bullet points
- [ ] All tests pass: pytest -q
- [ ] Pre-commit hooks pass: pre-commit run --all-files
- [ ] Lint and type checks pass: ruff check src/; mypy src/

## After running ./scripts/release.sh <version>:
- [ ] Tag pushed to origin
- [ ] GitHub Release created with changelog notes
- [ ] Artifacts attached to release (wheel and sdist)
- [ ] Smoke test performed: install package from release and run basic commands
