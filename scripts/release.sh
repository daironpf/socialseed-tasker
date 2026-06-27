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

# Build new changelog
TMPFILE="$(mktemp)"
{
  # Print everything up to and including Unreleased header
  awk '1; /^## \\[Unreleased\\]/ { exit }' CHANGELOG.md
  echo ""
  echo "## [v${NEW_VERSION}] - ${DATE}"
  echo ""
  echo "${UNRELEASED_CONTENT}"
  echo ""
  # Print everything after Unreleased section (skip empty line after header)
  awk 'BEGIN{skip=0} /^## \\[Unreleased\\]/{skip=1; next} /^## \\[v[0-9]+\\.[0-9]+\\.[0-9]+\\]/{skip=0} { if(skip==0) print }' CHANGELOG.md | tail -n +2
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
