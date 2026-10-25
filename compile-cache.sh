#!/bin/bash
# Offline cache compilation only; the cache is private and never pruned.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
MODE="${1:---dry-run}"
if [ "$#" -gt 0 ]; then shift; fi
JOBS="${1:-4}"
case "$JOBS" in ''|*[!0-9]*) echo "Jobs must be a positive integer" >&2; exit 2;; esac
test "$JOBS" -gt 0
BASE="$(python3 - "$ROOT" "${HIGHBALL_ROOT:-}" <<'PY'
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(sys.argv[1]) / 'scripts'))
import adapter
base = pathlib.Path(sys.argv[2]) if sys.argv[2] else adapter.default_highball_root()
print(base.expanduser().resolve())
PY
)"
CACHE="$BASE/bottles/Detroit Isolated/.detroit-cache/msl"
if [ -n "${METAL_TOOL:-}" ]; then
    if [ ! -f "$METAL_TOOL" ] || [ ! -x "$METAL_TOOL" ]; then
        echo "METAL_TOOL must name an executable file." >&2
        exit 1
    fi
else
    METAL_TOOL="$BASE/.detroit-adapter/tools/Metal.xctoolchain/usr/bin/metal"
    if [ -x "$METAL_TOOL" ]; then
        python3 "$ROOT/scripts/prepare_metal.py" --verify --highball-root "$BASE"
    elif ! METAL_TOOL="$(xcrun -sdk macosx -find metal 2>/dev/null)"; then
        echo "Metal Toolchain unavailable; run ./prepare-metal.sh --dry-run, then --apply." >&2
        exit 1
    fi
fi
export METAL_TOOL
case "$MODE" in
    --dry-run)
        printf 'Would compile private cache: %s\nJobs: %s\n' "$CACHE" "$JOBS"
        "$METAL_TOOL" --version
        ;;
    --apply)
        "$ROOT/verify.sh" --highball-root "$BASE"
        if ps -axo comm= | /usr/bin/grep -F "$BASE/engines/detroit-strict-003-r28/" | /usr/bin/grep -E '/(wine|wineserver)$' >/dev/null; then
            echo "Close Detroit Isolated before compiling cache; other environments can stay open." >&2; exit 1
        fi
        mkdir -p "$ROOT/logs"
        LOG="$(mktemp "$ROOT/logs/compile-cache.XXXXXX")"
        /bin/bash "$ROOT/vendor/compile_msl_library_cache.sh" -j "$JOBS" "$CACHE" 2>&1 | tee "$LOG"
        ;;
    *) echo "Usage: compile-cache.sh [--dry-run|--apply] [jobs]" >&2; exit 2;;
esac
