# Detroit: Become Human — audio fixes

[简体中文](README.zh-CN.md)

The v0.4 candidate combines safe XAudio2 device-query/voice-creation failure handling with runtime default-output following. It updates `xaudio2_8.dll` and `mmdevapi.dll` in the existing **Detroit Isolated** engine and bottle, and enables the private default-output setting. It preserves the existing voice graph while rebuilding a failed or changed output stream.

## Use

The full release archive includes this folder as `audio/`. If the isolated environment is already installed, download `highball-detroit-audiofix-v0.4.1-preview.1-macos-x86_64.tar.gz` and `SHA256SUMS` from the [release](https://github.com/jason312928/highball-detroit-adapter/releases/tag/v0.4.1-preview.1). Check the archive’s matching SHA-256 entry, extract it and open Terminal in the extracted `highball-detroit-audiofix-v0.4.1-preview.1` folder. The archive contains the DLL; the Git source checkout does not.

For an audio-only download, paste this block into Terminal. It stops if that version is already extracted; use the existing folder in that case.

```bash
(
  set -e
  mkdir -p "$HOME/Downloads/highball-detroit-setup"
  cd "$HOME/Downloads/highball-detroit-setup"
  test ! -e highball-detroit-audiofix-v0.4.1-preview.1
  RELEASE="https://github.com/jason312928/highball-detroit-adapter/releases/download/v0.4.1-preview.1"
  ASSET="highball-detroit-audiofix-v0.4.1-preview.1-macos-x86_64.tar.gz"
  curl --fail --location --output "$ASSET" "$RELEASE/$ASSET"
  curl --fail --location --output SHA256SUMS "$RELEASE/SHA256SUMS"
  awk -v asset="$ASSET" '$2 == asset { print; found=1 } END { if (!found) exit 1 }' \
    SHA256SUMS > selected.sha256
  shasum -a 256 -c selected.sha256
  tar -xzf "$ASSET"
  cd highball-detroit-audiofix-v0.4.1-preview.1
  shasum -a 256 -c SHA256SUMS
)
```

Then enter the audio folder (or `audio/` inside the full bundle):

```bash
cd "$HOME/Downloads/highball-detroit-setup/highball-detroit-audiofix-v0.4.1-preview.1"
```

On the reviewed baseline, close Detroit and the private Windows Steam/Wine programs, then run:

```bash
./install.sh --dry-run &&
./install.sh --apply &&
./verify.sh
```

Paths containing spaces and a custom `--highball-root` are supported. Scripts default to dry-run, verify the reviewed x86_64 DLL hashes, back up all four prior files and the routing preference, recover partial writes, and reject conflicting user changes. Logs stay in `logs/`.

The standard `install.sh`, `verify.sh` and `rollback.sh` now operate on routing v2. They are equivalent to the explicit `install-routing.sh`, `verify-routing.sh` and `rollback-routing.sh` commands. Source Git checkouts contain no compiled DLLs; use a release bundle.

## Rollback

Close Detroit and its private Steam, then run:

```bash
./rollback.sh --dry-run
./rollback.sh --apply
```

Backups are under `.detroit-adapter/audio-routing-v2/`. Rollback restores the state before this update, including an older v1 patch if that was installed. To remove that older patch as well, subsequently run `python3 audiofix.py rollback --apply`. Restore audio before archiving the entire isolated adapter.

## Validation

Eight deterministic routing scenarios and endpoint identity/error/absence/resize/concurrency tests passed. A real silent buffer was consumed after the exact built PE images were verified in memory. The Python suite ran 46 tests: 45 passed and the optional CLI check was skipped. The five patches reconstruct the modified source files from the pinned archive.

Physical AirPods switching, physical sample-rate/channel changes and gameplay after this update remain unverified. The latest game exit, missing Vulkan vertex inputs and cinematic blur are not claimed fixed. See [routing details](routing/README.md), [source-lock.json](source-lock.json), [patches](patches/) and [build instructions](BUILD.md).

Wine changes retain LGPL-2.1-or-later; FAudio retains its upstream zlib-style license. [License notices](licenses/) and corresponding source are included. No game files, shaders, raw logs, saves, device identities or personal configuration are distributed.
