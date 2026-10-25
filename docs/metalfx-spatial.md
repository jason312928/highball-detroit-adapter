# Experimental Detroit MetalFX spatial scaling

[简体中文](zh-CN/metalfx-spatial.md)

This is an optional, separately built private-engine variant, not part of the v0.4.1 release archives. It does not add DLSS, temporal reconstruction or frame generation. Gameplay visuals and FPS remain unverified.

The patch reports a reduced Vulkan surface extent, renders into private textures at that extent, then encodes MetalFX spatial scaling and a copy to the display-size drawable. At the default 75% dimension ratio, scene output pixel count is approximately 56% of native, with even-size rounding. This does not guarantee that every internal game pass scales or predict FPS. UI is part of the scaled frame; clarity and input mapping require game testing.

No Vulkan features or missing vertex attributes are fabricated. Unsupported formats, inconsistent extents, scaler creation and allocation failures are reported rather than claimed successful. The reviewed game output format is BGRA8Unorm; the implementation also permits RGBA8Unorm and RGBA16Float, but those two formats have not had the same presentation validation. Format or resize errors require investigating the log or restoring the original engine.

## Build and install

Use macOS 13+ with a MetalFX-capable device and a current SDK. First build the normal strict candidate using `build-cmake.sh` and its documented dependency layout. Then apply `patches/0002-detroit-metalfx-spatial.patch` to that source checkout and reconfigure its existing CMake build with `-DMVK_DETROIT_METALFX_DEFAULT=ON`. Build target `MoltenVK`. The CMake option defaults OFF in source; the private MetalFX variant must be deliberately built ON. Apple frameworks are linked from the system, not redistributed.

Before installing, compile `src/metalfx_swapchain_probe.m` as x86_64, using complete Vulkan headers, and link Foundation, Metal, MetalFX and QuartzCore. Pass the candidate dylib path as its only argument. Run with `MTL_DEBUG_LAYER=1` both normally and with `MVK_DTR_METALFX_SPATIAL=0`. This is an offscreen Vulkan presentation test, not a game launch. It tests both the recent game display geometry and a resize, copies actual drawable pixels back, and checks their color.

```bash
# Preview and then install only into an existing owned Detroit engine:
python3 -B scripts/metalfx_engine.py install --library /absolute/path/to/libMoltenVK.dylib
python3 -B scripts/metalfx_engine.py install --library /absolute/path/to/libMoltenVK.dylib --apply
python3 -B scripts/metalfx_engine.py verify
./verify.sh
# Restore the complete previous private engine library:
python3 -B scripts/metalfx_engine.py rollback
python3 -B scripts/metalfx_engine.py rollback --apply
```

Close Detroit before installation or rollback; these tools never start or stop it. The original engine library is independently backed up under the private adapter state at `metalfx-spatial-v1/original.dylib`. The original installation record remains unchanged. Verification accepts an override only with matching ownership, exact installed hash and an intact original backup. Another candidate requires restoring the original first. EXE, audio, saves and shader caches are not targets.

`MVK_DTR_METALFX_SPATIAL=0` disables the path for a fresh process. `MVK_DTR_METALFX_SCALE` accepts 0.5 through values below 1; default is 0.75. Invalid values use 0.75. Changing inherited environment settings requires a fresh game process and correct Highball/Steam environment propagation. A full library rollback avoids that ambiguity. Do not clear existing caches.

The log must contain `[detroit-metalfx] ... enabled spatial input=... output=...` and `encoded frame=...` to establish that a game process actually used the path. Configuration verification alone does not establish that. Test the same scene with/without scaling, including subtitles, menus, mouse input, fullscreen, app switching and cinematic transitions. Missing vertex-input mappings and compilation stutters are separate unresolved issues.

Validation: x86_64/Rosetta, Metal API Validation, 24 presented frames and pixel checks at 1134×736 → 1512×982 and 960×600 → 1280×800; 24 frames without scaling at native extents. Eight synthetic installer transaction tests cover dry-run, repeat, restore, ownership/backup safety, running-game refusal and interrupted publication. No game was launched for these checks.
