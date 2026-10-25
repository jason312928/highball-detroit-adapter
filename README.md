# Detroit: Become Human on Highball

**MetalFX gameplay failure: the latest candidate produced a black screen with a purple edge in Detroit and has been withdrawn. Both private libraries were restored. Native and Windows Vulkan probes passed but did not establish game compatibility. There is currently no gameplay-validated MetalFX installation; the source remains experimental.**

MetalFX requires the paired Wine WSI fix; the earlier MoltenVK-only preview is withdrawn. Windows Vulkan regression tests now cover bootstrap, scaling, resize and disable through Wine.

Experimental: [MetalFX spatial scaling](docs/metalfx-spatial.md) is available as a separately built private-engine variant. Offscreen presentation validation passed; game visuals and FPS remain unverified.

Optional: [background blur workaround](docs/background-blur.md), with version checks, full EXE backup and rollback. Explicit user choice is required; gameplay visuals remain unverified. Available in current source, not the v0.4.1 release archives.

## Audio output routing — v0.4.1-preview.1

The new audio candidate follows the system default output during playback, rebuilds an invalidated WASAPI stream, and handles initialization failures without dereferencing failed COM results. It keeps the XAudio voice graph and mix format intact. It is installed only in the private Detroit engine and bottle.

Deterministic routing and endpoint tests, actual DLL loading, silent-buffer consumption, and transaction tests passed. **macOS default-output changes, physical AirPods reconnection and gameplay after this change are still unverified. The latest game exit and missing vertex-input mappings are not claimed fixed. Cinematic blur remains unconfirmed.**

For an existing isolated installation, see [audio routing](audio/routing/README.md). The original Metal cache is retained.


[简体中文](README.zh-CN.md)

An isolated compatibility adapter and diagnostics for **Detroit: Become Human** on [Highball](https://github.com/gauthierpiarrette/highball).

**Tested progress: the game passes the former 98% stop during initial shader compilation, reaches the main menu and enters a gameplay scene on the reviewed Highball engine.**

The original startup failure included this Metal vertex-input error:

~~~text
Vertex attribute in_vfMsBindPosePosition(12) is missing from the vertex descriptor.
~~~

**Status: preview. The latest run with the audio fix and persistent Metal cache was reported to play normally, without repeating the long shader compilation on every launch. Long-session stability, all-scene correctness and audio-device reconnection remain unverified.**

## Patch scope

The patch starts from MoltenVK-Detroit Release003, pins its SPIRV-Cross dependency, and records vertex-input and specialization state when pipeline creation fails. Missing inputs are rejected rather than assigned a default format and buffer binding. This retains failed-pipeline evidence; reaching a scene does not establish that every vertex-input mismatch is repaired.

The [XAudio2 fix](audio/README.md) handles failed audio-device queries and propagates mastering-voice creation errors. It addresses the identified audio access-violation path without inventing a device format or returning success for an invalid voice.

## Start here

**Already installed?** Open Highball → **Detroit: Become Human** → **Game settings**. Select **Play there** beside **Detroit Isolated** once; Highball remembers it, and subsequent launches use the normal **Play** button. To add the new audio fix, follow the [audio upgrade instructions](audio/README.md).

**First installation?** Follow the [step-by-step installation guide](docs/usage.md). It includes download commands, how to find your environment name and game folder, checks before installation, launch instructions and rollback. The prebuilt library does not require compiling MoltenVK or installing full Xcode.

The reviewed baseline is Highball 0.10.22 with x64-crossover26.3-r28 and the Windows Steam edition of the game. Installation copies the source environment, engine and game; allow space for all three plus at least 12 GiB spare, often more than 75 GiB. Original game files and the shared engine are preserved. Rollback retains the test environment's saves in an archive.

The [v0.4.1-preview.1 release](https://github.com/jason312928/highball-detroit-adapter/releases/tag/v0.4.1-preview.1) includes a complete installation archive and a smaller audio-only upgrade. The full bundle now includes `prepare-metal.sh`: it obtains and verifies a pinned Apple compiler privately, without full Xcode. Apple tools, Microsoft DLLs and game-specific shaders are not redistributed. Long-session stability is not established. Source compilation is optional and documented separately in [Build](docs/build.md).

## Validation

Initial compilation has progressed past 98%, with menu and scene entry. The persistent-cache build produced 28,635 Metal libraries; all loaded successfully, and a repeat compiler run built zero. Subsequent ordinary play was reported normal without repeated long startup compilation. File probes, compiler reuse and a user-reported game result are recorded separately in [Validation](docs/validation.md). See the [reproduction audit](docs/reproduction.md) for the exact flow, dependencies and remaining limits.

The normal route is **Highball → Detroit: Become Human → Play**, using the remembered `Detroit Isolated` environment. First-time setup must complete the game’s own shader pass **and then** the offline Metal cache step; skipping the latter reproduces slow repeat startups. No `.command` launcher, game-EXE patch or depth-of-field change is required.


## Development

~~~bash
make static
make test
~~~

Tests use temporary fixtures and do not start Wine or the game. Set HIGHBALL_TEST_CLI to include configuration decoding by an existing Highball CLI.

The local engine fingerprint is stored in the ignored engine-lock.local.json. Machine records, game files, shader dumps and runtime logs are not tracked.

- [patches/](patches): patch series and upstream reference diffs.
- [scripts/](scripts): installation transactions and diagnostic utilities.
- [src/](src): ABI probe and minimal reproductions.
- [tests/](tests): installer regression tests.
- [source-lock.json](source-lock.json): source revisions and input hashes.

## License

New scripts, tests and documentation are [MIT licensed](LICENSE). Upstream code retains its own licenses; see [Third-party notices](THIRD_PARTY_NOTICES.md).
