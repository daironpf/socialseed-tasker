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
  pre-commit run mypy --all-files

Common fixes:
- Formatting: run `black .` or `pre-commit run black --all-files`
- Import order: run `isort .` or `pre-commit run isort --all-files`
- Lint fixes: run `pre-commit run ruff --all-files` (ruff will auto-fix many issues)

CI integration:
- The CI workflow runs the same checks. Ensure your branch passes `pre-commit run --all-files` before opening a PR.
