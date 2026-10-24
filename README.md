# Detroit: Become Human on Highball

[简体中文](README.zh-CN.md)

Diagnostics and isolated MoltenVK testing for **Detroit: Become Human** on [Highball](https://github.com/gauthierpiarrette/highball).

The failure under investigation occurs during the game's first shader compilation: progress stalls at 98%, with Metal rejecting a vertex input missing from the pipeline descriptor.

~~~text
Vertex attribute in_vfMsBindPosePosition(12) is missing from the vertex descriptor.
~~~

**Status: diagnostic prerelease. Shader compilation completion, the main menu and scene rendering remain unverified.**

## Patch scope

The patch starts from MoltenVK-Detroit Release003, pins its SPIRV-Cross dependency, and records vertex-input and specialization state when pipeline creation fails. Missing inputs are rejected rather than assigned a default format and buffer binding. This preserves the failure for investigation; it does not implement a semantic fix for unbound attributes.

## Start here

**Already installed?** Open Highball → **Detroit Isolated** → **Detroit (isolated Steam)**. You do not need to build or install again.

**First installation?** Follow the [step-by-step installation guide](docs/usage.md). It includes download commands, how to find your environment name and game folder, checks before installation, launch instructions and rollback. The prebuilt library does not require compiling MoltenVK or installing full Xcode.

The reviewed baseline is Highball 0.10.22 with x64-crossover26.3-r28 and the Windows Steam edition of the game. Installation copies the source environment, engine and game; allow space for all three plus at least 5 GiB spare, typically more than 64 GiB. Original game files and the shared engine are preserved. Rollback retains the test environment's saves in an archive.

The download is a **diagnostic prerelease**, not a verified gameplay fix. Source compilation is optional and documented separately in [Build](docs/build.md).

## Validation

Complete library compilation, the Rosetta/Vulkan probe, isolated installation and actual game-process library loading have been verified. Game-level acceptance remains open. The distinction and remaining work are documented in [Validation](docs/validation.md) and [Vertex input](docs/vertex-input.md).

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
