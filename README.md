# Detroit: Become Human on Highball

[简体中文](README.zh-CN.md)

An isolated compatibility adapter and diagnostics for **Detroit: Become Human** on [Highball](https://github.com/gauthierpiarrette/highball).

**Tested progress: the game passes the former 98% stop during initial shader compilation, reaches the main menu and enters a gameplay scene on the reviewed Highball engine.**

The original startup failure included this Metal vertex-input error:

~~~text
Vertex attribute in_vfMsBindPosePosition(12) is missing from the vertex descriptor.
~~~

**Status: preview. Visual and scene-input issues remain open. The new audio fix has passed failure-injection and runtime audio tests; gameplay after that fix and long-session stability still require validation.**

## Patch scope

The patch starts from MoltenVK-Detroit Release003, pins its SPIRV-Cross dependency, and records vertex-input and specialization state when pipeline creation fails. Missing inputs are rejected rather than assigned a default format and buffer binding. This retains failed-pipeline evidence; reaching a scene does not establish that every vertex-input mismatch is repaired.

The [XAudio2 fix](audio/README.md) handles failed audio-device queries and propagates mastering-voice creation errors. It addresses the identified audio access-violation path without inventing a device format or returning success for an invalid voice.

## Start here

**Already installed?** Open Highball → **Detroit Isolated** → **Detroit (isolated Steam)**. To add the new audio fix, follow the [audio upgrade instructions](audio/README.md).

**First installation?** Follow the [step-by-step installation guide](docs/usage.md). It includes download commands, how to find your environment name and game folder, checks before installation, launch instructions and rollback. The prebuilt library does not require compiling MoltenVK or installing full Xcode.

The reviewed baseline is Highball 0.10.22 with x64-crossover26.3-r28 and the Windows Steam edition of the game. Installation copies the source environment, engine and game; allow space for all three plus at least 5 GiB spare, typically more than 64 GiB. Original game files and the shared engine are preserved. Rollback retains the test environment's saves in an archive.

The [v0.2.0-preview.1 release](https://github.com/jason312928/highball-detroit-adapter/releases/tag/v0.2.0-preview.1) includes a complete installation archive and a smaller audio-only upgrade. Daily gameplay stability is not established. Source compilation is optional and documented separately in [Build](docs/build.md).

## Validation

Initial shader compilation has progressed past 98%, and an interactive run reached the menu and a scene. Library compilation, loading, transactional installation and the new audio failure paths have also been tested. Visual correctness, scene input, audio-device reconnection during gameplay and long-session stability remain open. The distinction and remaining work are documented in [Validation](docs/validation.md) and [Vertex input](docs/vertex-input.md).

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
