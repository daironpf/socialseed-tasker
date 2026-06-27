#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -lt 1 ]; then
  echo "Usage: $0 export|verify|restore|list [args]" >&2
  exit 2
fi
CMD="$1"
shift
echo "python -m socialseed_tasker.backup.cli $CMD $*" >&2
python -m socialseed_tasker.backup.cli "$CMD" "$@"
