# Runtime audio output routing

[简体中文](README.zh-CN.md)

This candidate updates `xaudio2_8.dll` and `mmdevapi.dll` in the Detroit-only engine and bottle. The system default render endpoint is checked every 500 ms on the audio worker. A new WASAPI stream uses the existing engine mix format with shared-mode automatic conversion, so source voices and queued audio remain owned by the existing XAudio engine. If reopening fails, the old working stream remains active; invalidated streams are released and retried. Shutdown remains interruptible when no output exists.

The opt-in setting is `HB_DETROIT_AUDIO_FOLLOW_DEFAULT=1`. The installer sets it only in Detroit Isolated. Explicit Wine registry output preferences remain respected. AirPods must be connected and selected as the macOS output; this does not force Bluetooth pairing or select a system output for the user.

## Existing installation

Close the game and Steam in Detroit Isolated first. From the adapter directory:

```bash
./audio/install-routing.sh --dry-run
./audio/install-routing.sh --apply
./audio/verify-routing.sh
```

Start normally from Highball. If private Steam was already running before the installation, exit it and start again so the setting is inherited. No shader-cache deletion or recompilation is requested by this audio update.

```bash
./audio/rollback-routing.sh --dry-run
./audio/rollback-routing.sh --apply
```

Rollback verifies and restores all four previous DLLs and the previous value of the routing setting, preserving unrelated settings. To remove the older v1 audio patch too, run its rollback only after routing rollback. An interrupted installation is recoverable on the next `--apply`; conflicting user changes are rejected.

## Evidence and limits

Eight routing scenarios cover default changes, explicitly fixed outputs, failed replacement/retry, endpoint invalidation, temporary absence and service initialization failures. Endpoint tests cover identity preservation, failure/absence, buffer resizing and concurrent reuse. Real DLL image timestamps were checked against the built artifacts; a real silent XAudio buffer was consumed. Installer tests cover partial write recovery, rollback, settings preservation and path tampering.

Physical AirPods reconnection, sample-rate/channel changes on a physical device, and gameplay stability remain unverified. There is no proof that the latest exit code 1 was caused by audio. Missing Vulkan vertex attributes and cinematic blur remain unresolved; this update does not fabricate attributes or alter the game executable.
