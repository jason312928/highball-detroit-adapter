#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT/logs"
LOG="$(mktemp "$ROOT/logs/prepare-metal.XXXXXX")"
python3 "$ROOT/scripts/prepare_metal.py" "$@" 2>&1 | tee "$LOG"
