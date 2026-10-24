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
| Initial shader compilation past the former 98% stop | Passed in the reviewed interactive run; game proceeded to menu and scene |
| Main menu | Reached; menu clicking worked in the interactive test |
| Gameplay scene | Entered; full interaction and scene correctness are not accepted |
| Visual correctness | Highlight clipping observed; SDR comparison prepared, result pending |
| Scene mouse input | Interaction issue observed; gesture instructions supplied, resolution unverified |
| Audio crash diagnosis | Dump, registers and disassembly identify a failed mix-format query followed by a null dereference in FAudio; Wine also ignored voice-creation failure |
| Audio failure-path tests | Pre-patch failures reproduced; patched device-query and wrapper cases passed |
| Installed audio DLL | x86_64 load, mastering-voice creation and silent-buffer consumption passed |
| Gameplay after audio fix / device reconnection | Not yet tested |
| Long-session stability | Open; a pre-fix run ended with access violation |
| Offline Metal cache | Not exercised; metal compiler unavailable |

These are local engineering observations, not a cross-platform compatibility claim. Machine snapshots and original logs are not published. Build success and library-load evidence are recorded separately from game-level acceptance. The later interactive run establishes progress beyond 98%, menu access and scene entry. It also exposed visual/input defects and an audio access violation. Those startup observations predate the audio fix; they do not establish post-fix gameplay or long-session stability. No success is inferred from an empty error scan.

The [audio documentation](../audio/README.md) separates source-level failure-injection tests from actual DLL/audio probes. Original logs, dumps, screenshots, device identifiers and machine records remain private.

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
