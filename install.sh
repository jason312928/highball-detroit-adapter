#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT/logs"
LOG="$(mktemp "$ROOT/logs/install.XXXXXX")"
python3 -u "$ROOT/scripts/adapter.py" install "$@" 2>&1 | tee "$LOG"
