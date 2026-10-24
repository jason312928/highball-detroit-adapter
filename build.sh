#!/bin/bash
# Builds a diagnostic candidate only. It does not install or launch Wine.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
BASE=8b511fdc5351a37c305bc246e161796ddca56b18
SPIRV=05583ac1537d777d304128142de2365bfa4a38df
SOURCE="${1:-$ROOT/work/MoltenVK-Detroit}"
SOURCE="$(cd "$SOURCE" && pwd)"
if ! xcodebuild -version >/dev/null 2>&1; then
    exec /bin/bash "$ROOT/build-cmake.sh" "$SOURCE"
fi
mkdir -p "$ROOT/logs" "$ROOT/build"
LOG="$(mktemp "$ROOT/logs/build.XXXXXX")"
exec > >(tee "$LOG") 2>&1
echo "Build log: $LOG"
test "$(git -C "$SOURCE" rev-parse HEAD)" = "$BASE"
PATCH="$ROOT/patches/0001-strict-interfaces-and-pinned-spirv.patch"
if git -C "$SOURCE" apply --check "$PATCH" 2>/dev/null; then
    git -C "$SOURCE" apply "$PATCH"
else
    git -C "$SOURCE" apply --reverse --check "$PATCH"
fi
git -C "$SOURCE" diff --check
# Refuse unrelated changes in a source checkout supplied by the caller.
EXPECTED="$(mktemp "$ROOT/build/expected.XXXXXX")"
git -C "$SOURCE" diff --binary > "$EXPECTED"
cmp "$PATCH" "$EXPECTED"
rm "$EXPECTED"
echo "Pinned MoltenVK=$BASE SPIRV-Cross=$SPIRV; strict interface patch applied."
xcodebuild -version
xcrun -sdk macosx -find metal
cd "$SOURCE"
./fetchDependencies --macos
test "$(git -C External/SPIRV-Cross rev-parse HEAD)" = "$SPIRV"
test -z "$(git -C External/SPIRV-Cross status --porcelain)"
xcodebuild build -project MoltenVKPackaging.xcodeproj \
    -scheme "MoltenVK Package (macOS only)" -destination "generic/platform=macOS" \
    -configuration Release ARCHS=x86_64 ONLY_ACTIVE_ARCH=NO \
    -derivedDataPath "$ROOT/build/DerivedData" \
    CODE_SIGNING_ALLOWED=NO
DYLIB="$SOURCE/Package/Release/MoltenVK/dynamic/dylib/macOS/libMoltenVK.dylib"
test -f "$DYLIB"
lipo "$DYLIB" -verify_arch x86_64
cp "$DYLIB" "$ROOT/build/libMoltenVK.dylib"
xcrun clang -Wall -Wextra -Werror -arch x86_64 -D_DARWIN_C_SOURCE \
    -I "$ROOT/src/include" "$ROOT/src/probe.c" -o "$ROOT/build/probe-x86_64"
MVK_CONFIG_LOG_LEVEL=1 MVK_CONFIG_SHADER_COMPRESSION_ALGORITHM=3 \
    MVK_CONFIG_SHOULD_MAXIMIZE_CONCURRENT_COMPILATION=1 \
    "$ROOT/build/probe-x86_64" "$ROOT/build/libMoltenVK.dylib"
python3 - "$ROOT" "$BASE" "$SPIRV" <<'PY'
import hashlib,json,pathlib,sys
p=pathlib.Path(sys.argv[1])
lib=p/'build/libMoltenVK.dylib'
if b'HB_DETROIT_STRICT_INTERFACE_V1' not in lib.read_bytes():
    raise SystemExit('strict marker missing')
h=lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
m=dict(policy='strict-interface-v1',dylib=lib.name,sha256=h(lib),
       moltenvk_commit=sys.argv[2],spirv_cross_commit=sys.argv[3],
       patch_sha256=h(p/'patches/0001-strict-interfaces-and-pinned-spirv.patch'),
       probe_passed=True,game_validated=False,purpose='diagnostic; no invented vertex inputs')
(p/'build/candidate.json').write_text(json.dumps(m,indent=2)+'\n')
PY
echo "Built diagnostic candidate: $ROOT/build/candidate.json. Gameplay remains unverified."
