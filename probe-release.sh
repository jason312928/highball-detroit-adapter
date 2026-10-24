#!/bin/bash
# Independent Rosetta probe. Does not invoke Wine or open any game files.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT/logs" "$ROOT/build"
LOG="$(mktemp "$ROOT/logs/probe.XXXXXX")"
exec > >(tee "$LOG") 2>&1
DYLIB="$ROOT/vendor/release003-probe-only.dylib"
EXPECTED=e736ba7881750333624f86b2253532f968f4dd67cc56fb91a24b9ab6134db386
ACTUAL="$(shasum -a 256 "$DYLIB" | awk '{print $1}')"
test "$EXPECTED" = "$ACTUAL"
file "$DYLIB"
lipo "$DYLIB" -verify_arch x86_64
otool -arch x86_64 -L "$DYLIB"
xcrun clang -Wall -Wextra -Werror -arch x86_64 -D_DARWIN_C_SOURCE \
    -I "$ROOT/src/include" "$ROOT/src/probe.c" -o "$ROOT/build/probe-x86_64"
MVK_CONFIG_LOG_LEVEL=1 \
MVK_CONFIG_SHADER_COMPRESSION_ALGORITHM=3 \
MVK_CONFIG_SHOULD_MAXIMIZE_CONCURRENT_COMPILATION=1 \
"$ROOT/build/probe-x86_64" "$DYLIB"
