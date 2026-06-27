#!/usr/bin/env bash
set -euo pipefail

ARTIFACT="$1"
if [ -z "${RELEASE_GPG_PRIVATE_KEY:-}" ]; then
  echo "RELEASE_GPG_PRIVATE_KEY not set"
  exit 1
fi
echo "$RELEASE_GPG_PRIVATE_KEY" | base64 --decode > private.key
gpg --batch --import private.key
gpg --batch --yes --passphrase "$RELEASE_GPG_PASSPHRASE" -o "${ARTIFACT}.asc" --detach-sign "$ARTIFACT"
echo "Signed ${ARTIFACT}"
