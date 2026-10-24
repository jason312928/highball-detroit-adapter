# Validation

[简体中文](zh-CN/validation.md)

## Software baseline

Highball 0.10.22 with x64-crossover26.3-r28; MoltenVK-Detroit Release003 plus the patch series; SPIRV-Cross 05583ac1537d777d304128142de2365bfa4a38df. Complete revisions and input hashes are in [source-lock.json](../source-lock.json).

The Release003 distribution reports a dirty MoltenVK source tree. Its tag alone cannot reproduce that binary exactly; this project builds a separately identified diagnostic variant.

## Recorded checks

| Check | Result / scope |
|---|---|
| Full library build | CMake backend compiled and linked with SPIRV-Tools and cereal enabled |
| Runtime probe | Rosetta load, configuration readback, Vulkan instance creation and device enumeration passed |
| Isolated installer | Installation, hash checks and repeated execution passed |
| Game-process load | Independent EXE and dylib paths confirmed by dyld/lsof; architecture confirmed by sampling |
| First shader compilation completed | Unverified |
| Main menu, scene and visual correctness | Unverified |
| Offline Metal cache | Not exercised; metal compiler unavailable |

These are local engineering observations, not a cross-platform compatibility claim. Machine snapshots and original logs are not published. Build success and library-load evidence are recorded separately from game-level acceptance. The first run ended before shader/menu/scene acceptance; no success is inferred from an empty error scan.

## Regression tests

~~~bash
make static
make test
HIGHBALL_TEST_CLI="/path/to/highball" make test
~~~

Tests require macOS clang/lipo and use temporary synthetic fixtures. They do not launch Wine or the game. Without HIGHBALL_TEST_CLI, the optional CLI decoding test is skipped. Coverage includes hash/architecture rejection, paths with spaces, transaction recovery, repeat installation and rollback.

## Minimal Metal reproduction

~~~bash
mkdir -p build
xcrun clang -arch x86_64 -fobjc-arc -framework Foundation -framework Metal \
  src/metal_descriptor_repro.m -o build/metal-repro
./build/metal-repro
~~~

A zero exit status means the expected rejection was reproduced, not that the game was repaired.
