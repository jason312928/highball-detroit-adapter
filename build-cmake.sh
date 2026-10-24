#!/bin/bash
# Build using Command Line Tools; no system install, sudo, or offline Metal compiler.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
WORK="$(cd "$ROOT/work" && pwd)"
SOURCE="${1:-$WORK/MoltenVK-Detroit}"
TOOLS="$WORK/build-tools/bin"
mkdir -p "$ROOT/logs" "$ROOT/build"
LOG="$(mktemp "$ROOT/logs/build-cmake.XXXXXX")"
exec > >(tee "$LOG") 2>&1
echo "CMake build log: $LOG"
test "$(git -C "$SOURCE" rev-parse HEAD)" = 8b511fdc5351a37c305bc246e161796ddca56b18
test "$(git -C "$WORK/SPIRV-Cross" rev-parse HEAD)" = 05583ac1537d777d304128142de2365bfa4a38df
test -z "$(git -C "$WORK/SPIRV-Cross" status --porcelain)"
PATCH="$ROOT/patches/0001-strict-interfaces-and-pinned-spirv.patch"
git -C "$SOURCE" apply --reverse --check "$PATCH"
EXPECTED="$(mktemp "$ROOT/build/expected-cmake.XXXXXX")"
git -C "$SOURCE" diff --binary > "$EXPECTED"
cmp "$PATCH" "$EXPECTED"
rm "$EXPECTED"
"$TOOLS/python" - "$ROOT" "$WORK" <<'PY'
import hashlib,json,pathlib,sys
k=pathlib.Path(sys.argv[1]);w=pathlib.Path(sys.argv[2])
lock=json.loads((k/'source-lock.json').read_text())
for filename,expected in lock['cmake_build']['inputs'].items():
    p=w/pathlib.Path(filename).name
    actual=hashlib.sha256(p.read_bytes()).hexdigest()
    if actual!=expected:raise SystemExit('Input checksum mismatch: '+str(p))
PY
"$TOOLS/cmake" -S "$SOURCE" -B "$WORK/mvk-cmake" -G Ninja \
    -D CMAKE_MAKE_PROGRAM="$TOOLS/ninja" -D CMAKE_BUILD_TYPE=Release \
    -D CMAKE_OSX_ARCHITECTURES=x86_64 -D CMAKE_OSX_DEPLOYMENT_TARGET=11.0 \
    -D CMAKE_POLICY_VERSION_MINIMUM=3.5 -D CPM_SOURCE_CACHE="$WORK/cpm-cache" \
    -D CPM_SPIRV-Cross_SOURCE="$WORK/SPIRV-Cross" \
    -D CPM_SPIRV-Tools_SOURCE="$WORK/spirv-tools" \
    -D CPM_SPIRV-Headers_SOURCE="$WORK/spirv-headers" \
    -D CPM_Vulkan-Headers_SOURCE="$WORK/headers" \
    -D CPM_cereal_SOURCE="$WORK/cereal" \
    -D SPIRV-Headers_SOURCE_DIR="$WORK/spirv-headers" \
    -D SPIRV_SKIP_TESTS=ON -D SPIRV_SKIP_EXECUTABLES=ON \
    -D SPIRV_WERROR=OFF -D JUST_INSTALL_CEREAL=ON
"$TOOLS/cmake" --build "$WORK/mvk-cmake" --target MoltenVK -j 6
cp "$WORK/mvk-cmake/MoltenVK/libMoltenVK.1.4.2.dylib" "$ROOT/build/libMoltenVK.dylib"
lipo "$ROOT/build/libMoltenVK.dylib" -verify_arch x86_64
xcrun clang -arch x86_64 -D_DARWIN_C_SOURCE -I "$ROOT/src/include" \
    "$ROOT/src/probe.c" -o "$ROOT/build/probe-x86_64"
MVK_CONFIG_LOG_LEVEL=1 MVK_CONFIG_SHADER_COMPRESSION_ALGORITHM=3 \
    MVK_CONFIG_SHOULD_MAXIMIZE_CONCURRENT_COMPILATION=1 \
    "$ROOT/build/probe-x86_64" "$ROOT/build/libMoltenVK.dylib"
"$TOOLS/python" - "$ROOT" <<'PY'
import hashlib,json,pathlib,sys
k=pathlib.Path(sys.argv[1]);h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=json.loads((k/'source-lock.json').read_text())
m=dict(policy='strict-interface-v1',dylib='libMoltenVK.dylib',
    sha256=h(k/'build/libMoltenVK.dylib'),moltenvk_commit=d['moltenvk_detroit']['commit'],
    spirv_cross_commit=d['spirv_cross']['commit'],
    patch_sha256=h(k/'patches/0001-strict-interfaces-and-pinned-spirv.patch'),
    probe_passed=True,game_validated=False,purpose='diagnostic; no invented vertex inputs',
    build_backend='CMake/Ninja/CommandLineTools',complete_source_compilation=True)
(k/'build/candidate.json').write_text(json.dumps(m,indent=2)+'\n')
print('Diagnostic candidate built and probed; gameplay remains unverified.')
PY
