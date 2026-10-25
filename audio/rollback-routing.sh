#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
exec python3 -u "$ROOT/routingfix.py" rollback "$@"
