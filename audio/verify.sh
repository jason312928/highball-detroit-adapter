#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
OPERATION="$(basename "$0" .sh)"
mkdir -p "$ROOT/logs"
LOG="$(mktemp "$ROOT/logs/$OPERATION.XXXXXX")"
python3 -u "$ROOT/audiofix.py" "$OPERATION" "$@" 2>&1 | tee "$LOG"
