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
| Gameplay scene | Entered; latest ordinary gameplay reported normal; every-scene coverage not recorded |
| Visual correctness | Earlier clipping report retained as history; latest ordinary play reported normal, controlled same-scene comparison not recorded |
| Scene mouse input | Earlier interaction report retained as history; latest ordinary play reported normal, individual gesture coverage not recorded |
| Audio crash diagnosis | Dump, registers and disassembly identify a failed mix-format query followed by a null dereference in FAudio; Wine also ignored voice-creation failure |
| Audio failure-path tests | Pre-patch failures reproduced; patched device-query and wrapper cases passed |
| Installed audio DLL | x86_64 load, mastering-voice creation and silent-buffer consumption passed |
| Gameplay after audio fix | Latest ordinary play reported normal after cache preparation |
| Physical audio-device reconnection | Not yet tested |
| Long-session stability | Open; a pre-fix run ended with access violation |
| Offline Metal cache | 28,635 built and accepted by Metal; repeat built 0 / skipped 28,635 |
| Private compiler preparation | Pinned Apple 17A324 archive/hash/signature, separate-layout installation, reuse and archive rollback passed |
| Normal Highball Play | UI and persisted environment select Detroit Isolated; command launcher unnecessary |

These checks combine engineering probes with an explicitly identified user report. The latest report confirms ordinary play without the previous repeated long startup compilation. It does not supply duration, complete scene/input coverage or a physical audio-device reconnection test. An absence of error lines alone is not treated as game success. Earlier visual/input and audio-crash observations are retained as history; the current workflow does not patch the game EXE or disable depth of field.

The [reproduction audit](reproduction.md) maps each working component to a published step. A separate empty layout exercised actual Apple archive extraction, code-signature/hash validation and private compiler installation. This is not a factory-reset Mac or a second full game installation. Cross-device compatibility and long-session stability remain open.

The [audio documentation](../audio/README.md) separates source-level failure-injection tests from actual DLL/audio probes. Original logs, dumps, screenshots, device identifiers and machine records remain private.

## Regression tests

~~~bash
make static
make test
HIGHBALL_TEST_CLI="/path/to/highball" make test
~~~

Tests require macOS clang/lipo and use temporary synthetic fixtures. They do not launch Wine or the game. Without HIGHBALL_TEST_CLI, the optional CLI decoding test is skipped. The reviewed run passed 35 tests, including the optional CLI check. Coverage includes hash/architecture/runtime rejection, paths with spaces, transaction recovery, repeat installation, cache math/invariance options, failed-cache preservation and toolchain rollback.

## Minimal Metal reproduction

~~~bash
mkdir -p build
xcrun clang -arch x86_64 -fobjc-arc -framework Foundation -framework Metal \
  src/metal_descriptor_repro.m -o build/metal-repro
./build/metal-repro
~~~

A zero exit status means the expected rejection was reproduced, not that the game was repaired.

## v0.4 audio routing and graphics follow-up

The routing candidate passed compilation, eight deterministic stream scenarios, endpoint identity/error/resize/concurrency tests and real silent-buffer playback with the exact built PE images. The Python suite ran 43 tests: 42 passed and the optional Highball CLI check was skipped. All five audio patches reconstruct the four modified source files exactly from the pinned archive.

An investigation of 48 locally captured vertex/fragment combinations found that 47 still require absent vertex inputs after dead-code pruning. That experiment is not deployed. No invented vertex attributes, scene modifications, EXE patch or cache deletion is part of this update. Cinematic local blur may resemble the depth-of-field issue discussed [upstream](https://github.com/KhronosGroup/MoltenVK/issues/2054#issuecomment-4660539730), but its cause has not been established here.

Physical AirPods output switching, physical format changes, the latest abnormal exit and gameplay stability after the routing update are not yet validated. A successful build or silent-buffer test is not a claim that the game is fully fixed.
