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

## Build and use

Follow [Build](docs/build.md) to prepare the pinned sources and dependencies, then:

~~~bash
./build.sh
python3 scripts/inspect_engine.py --source-bottle Games
./install.sh --dry-run --game-dir "/path/to/steamapps/common/Detroit Become Human" \
  --candidate-manifest "$PWD/build/candidate.json"
~~~

The installer checks hashes and architecture, then creates a separate engine, Bottle and game copy when --apply is supplied. Allow approximately 64 GiB plus cache space. Rollback archives the private environment and retains saves. See [Usage](docs/usage.md).

The local engine fingerprint is stored in the ignored engine-lock.local.json. Machine records, game files, shader dumps and runtime logs are not tracked.

## Validation

Complete library compilation, the Rosetta/Vulkan probe, isolated installation and actual game-process library loading have been verified. Game-level acceptance remains open. The distinction and remaining work are documented in [Validation](docs/validation.md) and [Vertex input](docs/vertex-input.md).

## Development

~~~bash
make static
make test
~~~

Tests use temporary fixtures and do not start Wine or the game. Set HIGHBALL_TEST_CLI to include configuration decoding by an existing Highball CLI.

- [patches/](patches): patch series and upstream reference diffs.
- [scripts/](scripts): installation transactions and diagnostic utilities.
- [src/](src): ABI probe and minimal reproductions.
- [tests/](tests): installer regression tests.
- [source-lock.json](source-lock.json): source revisions and input hashes.

## License

New scripts, tests and documentation are [MIT licensed](LICENSE). Upstream code retains its own licenses; see [Third-party notices](THIRD_PARTY_NOTICES.md).
