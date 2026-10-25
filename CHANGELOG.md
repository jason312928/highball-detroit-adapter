# Changelog

## Audio output routing — v0.4.0-preview.1

The new audio candidate follows the system default output during playback, rebuilds an invalidated WASAPI stream, and handles initialization failures without dereferencing failed COM results. It keeps the XAudio voice graph and mix format intact. It is installed only in the private Detroit engine and bottle.

Deterministic routing and endpoint tests, actual DLL loading, silent-buffer consumption, and transaction tests passed. **Physical AirPods switching and gameplay after this change are still unverified. The latest game exit and missing vertex-input mappings are not claimed fixed. Cinematic blur remains unconfirmed.**

For an existing isolated installation, see [audio routing](audio/routing/README.md). The original Metal cache is retained.


## v0.3.0-preview.1

- Use Highball’s normal game page and remembered environment choice; a command launcher is unnecessary.
- Accept an explicit Apple Metal compiler path for offline cache generation without changing the global Xcode selection.
- Limit cache-build process checks to the isolated engine, preserving other environments.
- Add cache compiler regression tests and a native Metal library-load probe.

[简体中文](CHANGELOG.zh-CN.md)

## v0.2.0-preview.1

- Tested startup now progresses past the former 98% initial shader-compilation stop and reaches the main menu and a gameplay scene on the reviewed engine.
- Add the XAudio2 device-query error-propagation fix and mastering-voice failure handling, with two independent source patches.
- Add a transactional, Detroit-only audio installer, verification and rollback; add seven synthetic installer regression tests.
- Supply a complete prebuilt installation archive, an audio-only upgrade and corresponding audio source.
- Update English and Chinese installation, validation and known-issue documentation.

Visual clipping, scene input and long-session stability remain open. Gameplay after the audio fix and physical audio-device reconnection have not completed validation. Existing MoltenVK vertex-input diagnostics can still appear.

## v0.1.0-diagnostic.1

Initial isolated MoltenVK diagnostic build, pinned SPIRV-Cross, transactional installation and 19 adapter regression tests. Initial publication did not yet include startup-to-scene validation.
