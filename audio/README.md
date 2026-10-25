# Detroit: Become Human — XAudio2 device-query fix

[简体中文](README.zh-CN.md)

Candidate fix for an access violation in Highball's CrossOver 26.3 XAudio2 implementation when an audio endpoint's mix-format query fails. This package is scoped to the existing **Detroit Isolated** environment and **detroit-strict-003-r28** engine.

## What changed

1. `FAudio_PlatformGetDeviceDetails` now handles failed endpoint/property/client/format queries, releases acquired resources and returns failure. The successful path retains the device's real format. A successful query with a null format is rejected.
2. `IXAudio2Impl_CreateMasteringVoice` now checks the underlying FAudio result. Failure leaves the output pointer null, releases the effect chain and returns failure; it no longer reports a valid voice after creation failed.

The first change follows upstream FAudio's [failure-propagation fix](https://github.com/FNA-XNA/FAudio/commit/67ed0a1eac0c52cc51e2bb892ccdb741d01bdec3), with balanced platform references. The second closes the Wine wrapper's error-propagation gap. See [patches](patches/) and [source-lock.json](source-lock.json).

## Use

The full release archive includes this folder as `audio/`. If the isolated environment is already installed, download `highball-detroit-audiofix-v0.3.0-preview.1-macos-x86_64.tar.gz` and `SHA256SUMS` from the [release](https://github.com/jason312928/highball-detroit-adapter/releases/tag/v0.3.0-preview.1). Check the archive’s matching SHA-256 entry, extract it and open Terminal in the extracted `highball-detroit-audiofix-v0.3.0-preview.1` folder. The archive contains the DLL; the Git source checkout does not.

For an audio-only download, paste this block into Terminal. It stops if that version is already extracted; use the existing folder in that case.

```bash
(
  set -e
  mkdir -p "$HOME/Downloads/highball-detroit-setup"
  cd "$HOME/Downloads/highball-detroit-setup"
  test ! -e highball-detroit-audiofix-v0.3.0-preview.1
  RELEASE="https://github.com/jason312928/highball-detroit-adapter/releases/download/v0.3.0-preview.1"
  ASSET="highball-detroit-audiofix-v0.3.0-preview.1-macos-x86_64.tar.gz"
  curl --fail --location --output "$ASSET" "$RELEASE/$ASSET"
  curl --fail --location --output SHA256SUMS "$RELEASE/SHA256SUMS"
  awk -v asset="$ASSET" '$2 == asset { print; found=1 } END { if (!found) exit 1 }' \
    SHA256SUMS > selected.sha256
  shasum -a 256 -c selected.sha256
  tar -xzf "$ASSET"
  cd highball-detroit-audiofix-v0.3.0-preview.1
  shasum -a 256 -c SHA256SUMS
)
```

Then enter the audio folder (or `audio/` inside the full bundle):

```bash
cd "$HOME/Downloads/highball-detroit-setup/highball-detroit-audiofix-v0.3.0-preview.1"
```

On the reviewed baseline, close Detroit and the private Windows Steam/Wine programs, then run:

```bash
./install.sh --dry-run &&
./install.sh --apply &&
./verify.sh
```

Paths containing spaces are supported. Use the same `--highball-root "/actual/Highball/data"` on all commands for a custom location. The installer requires the existing adapter's ownership markers, checks SHA-256 and PE architecture, backs up the two private DLLs and restores them on ordinary failure. Interrupted installs are recovered on the next `--apply`. Changed libraries are never overwritten blindly. Logs stay in `logs/`.

Only the private engine's built-in `xaudio2_8.dll` and the private Bottle's `system32` copy change. Shared engines, the source Bottle, game EXE, saves, global audio routing and device permissions are not changed. This audio package does not alter graphics settings.

After installation, use the normal **Detroit: Become Human** page in Highball. Under **Game settings**, use **Play there** beside `Detroit Isolated` once if needed; subsequent presses of **Play** use the remembered environment. Complete the [persistent Metal cache steps](../docs/usage.md) to avoid repeated long compilation. Ordinary gameplay after the audio fix and cache preparation was reported normal; device reconnection and long-session stress are still untested.

## Rollback

Close the game and private Windows Steam/Wine programs, then:

```bash
./rollback.sh --dry-run &&
./rollback.sh --apply
```

Original DLLs are retained under Highball's `.detroit-adapter/audio-v1/`. Roll back this audio fix **before** rolling back the entire Detroit adapter. After rollback, the environment uses its original audio implementation.

## Validation limits

- Original device-query function: reproduced the access violation with a failed format query and null result.
- Patched function: success, six API failures, success-with-null format and invalid index passed; resource counts balanced.
- Original Wine wrapper: reproduced incorrect success reporting after failed voice creation.
- Patched wrapper: failure, success and duplicate-voice cases passed.
- Installer: paths with spaces, repeated operations, injected write failure, interrupted recovery and conflict preservation passed.
- Built DLL: x86_64 PE, matching export names/ordinals, loaded in the current Wine engine; mastering-voice creation and silent-buffer consumption passed after installation.
- Ordinary gameplay after this audio fix and cache preparation: **reported normal**. Physical device reconnection and long-session stability: **not yet validated**.

The original low-level format query failed with `E_FAIL`. Its transient trigger has not been reproduced. The fix handles that failure; it does not guarantee that every game will recover audio or continue after receiving an initialization error. It does not resolve the separate MoltenVK input-mapping errors or establish daily gameplay readiness.

No raw runtime logs or crash dumps should be redistributed with this package. New installation scripts are MIT licensed. Wine changes retain LGPL-2.1-or-later and FAudio changes retain the upstream zlib-style license; complete notices are in [licenses](licenses/). The modified source is identified by the standalone patches. See [BUILD.md](BUILD.md) for reproduction.
