#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT/logs"
LOG="$(mktemp "$ROOT/logs/verify.XXXXXX")"
python3 -u "$ROOT/scripts/adapter.py" verify "$@" 2>&1 | tee "$LOG"
