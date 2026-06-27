#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev]"

echo "Running black"
python -m black --check .

echo "Running ruff"
ruff check src/

echo "Running unit tests"
pytest -q -k "not integration" --maxfail=1 --disable-warnings

echo "Building artifacts"
python -m build --sdist --wheel --outdir dist

echo "Docker build"
COMMIT=$(git rev-parse --short HEAD)
docker build -t tasker:${COMMIT} .

echo "Done"
