# Reproduction audit

[简体中文](zh-CN/reproduction.md)

The v0.3.0-preview.1 bundle contains the setup used for the current successful ordinary-play report. Follow [Install, launch and restore](usage.md) in order. The previous v0.2.0-preview.1 bundle lacked the private compiler preparation and complete cache instructions; editing its README alone would not reproduce the setup.

| Working component | How the published flow reproduces it |
|---|---|
| Highball 0.10.22 / CrossOver engine r28, x86_64 under Rosetta | Version prerequisite, source fingerprint and architecture checks before cloning; the private engine retains this Wine build |
| x64 Microsoft C++ runtime | Precondition and PE preflight for msvcp140, mfc140 and vcruntime140; reference version/hashes in source-lock.json; no Microsoft DLL redistribution |
| Independent engine, prefix and game | install.sh creates owned copies; preserves the original EXE and source caches; only the new copy’s first cache is renamed |
| Strict MoltenVK variant | Full bundle includes the same pinned dylib; SHA-256 and architecture checked, no invented vertex inputs |
| XAudio2 error propagation | Full bundle includes the matching x86_64 DLL and transactional audio installer; audio source and patches supplied |
| Compression 3 and concurrent compilation 1 | Installer sets both in the private engine/environment |
| Compiler without full Xcode | prepare-metal.sh downloads the Apple 17A324 archive, verifies pinned archive/compiler hashes and Apple signature, and installs privately; dry-run, reuse, failure cleanup and archive rollback included |
| First game compilation | User starts the native Highball entry once and waits for completion before exiting game and private Steam |
| Persistent Metal cache | compile-cache.sh preserves metadata math/invariance flags, writes .metallib atomically and skips newer existing outputs; do not clear caches on future launches |
| Normal launch | Highball game page → Game settings → Play there beside Detroit Isolated once; future main Play remembers the environment |
| Graphics and input | No mandatory graphics change, game-EXE edit or depth-of-field patch. Any future comparison is separate from this installation |
| Removal | Private tools archived first, audio reverted, then private engine/prefix/game archived; shared installations preserved |

## Evidence and boundary

The reference cache contains 28,635 compiled libraries, all accepted by native Metal. A repeat compiler pass built zero and skipped all 28,635. A later ordinary-play report confirms normal operation without repeating the long shader pass. Library paths in the corresponding game logs identify the private MoltenVK. These are separate evidence types; the report is not inferred from a successful build.

The packaged compiler-preparation script was also run in a separate empty layout with a verified local copy of the pinned Apple archive, including signature validation, repeat installation and rollback. Automated tests use synthetic engine/game/runtime fixtures and do not start Wine or a game. Package checks exercise the actual download instructions, hashes, extraction, real Metal compilation/loading and script dry-runs.

This does **not** certify an end-to-end game installation on a factory-reset Mac or every Apple GPU. Highball/engine updates need another audit. New scenes, changed settings, a different GPU or software updates can create additional shaders. Exact initial counts and startup times may vary. Long sessions, every-scene graphics/input coverage and physical audio-device reconnection remain unverified.

Apple tools, Microsoft runtimes, Steam credentials, saves, game files, generated shaders, raw runtime logs and machine snapshots are not in the public bundle. Each installation generates its own GPU-specific cache. Apple asset metadata in the toolchain lock is public distribution information.
