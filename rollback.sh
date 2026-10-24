#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT/logs"
LOG="$(mktemp "$ROOT/logs/rollback.XXXXXX")"
python3 -u "$ROOT/scripts/adapter.py" rollback "$@" 2>&1 | tee "$LOG"
