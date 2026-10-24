#!/bin/bash
# Offline cache compilation only; the cache is private and never pruned.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
MODE="${1:---dry-run}"
if [ "$#" -gt 0 ]; then shift; fi
JOBS="${1:-4}"
case "$JOBS" in ''|*[!0-9]*) echo "Jobs must be a positive integer" >&2; exit 2;; esac
test "$JOBS" -gt 0
BASE="${HIGHBALL_ROOT:-$HOME/Library/Application Support/Highball}"
CACHE="$BASE/bottles/Detroit Isolated/.detroit-cache/msl"
case "$MODE" in
    --dry-run)
        printf 'Would compile private cache: %s\nJobs: %s\n' "$CACHE" "$JOBS"
        if ! xcrun -sdk macosx -find metal; then
            echo "Metal Toolchain unavailable; no cache files changed." >&2
            exit 1
        fi
        ;;
    --apply)
        "$ROOT/verify.sh" --highball-root "$BASE"
        if ps -axo comm= | /usr/bin/grep -E '(/wine|/wineserver|\.exe)$' >/dev/null; then
            echo "Close Wine programs before compiling cache." >&2; exit 1
        fi
        mkdir -p "$ROOT/logs"
        LOG="$(mktemp "$ROOT/logs/compile-cache.XXXXXX")"
        /bin/bash "$ROOT/vendor/compile_msl_library_cache.sh" -j "$JOBS" "$CACHE" 2>&1 | tee "$LOG"
        ;;
    *) echo "Usage: compile-cache.sh [--dry-run|--apply] [jobs]" >&2; exit 2;;
esac
