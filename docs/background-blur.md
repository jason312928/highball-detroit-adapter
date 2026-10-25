# Optional background blur workaround

[简体中文](zh-CN/background-blur.md)

This changes the game EXE and requires explicit user choice. It is separate from the MoltenVK adapter and is not required for installation or startup. Gameplay visual validation is pending; no FPS improvement or vertex-input repair is claimed.

The [upstream guide](https://github.com/DiAvisoo/MoltenVK-Detroit/blob/8b511fdc5351a37c305bc246e161796ddca56b18/README.md) recommends setting `DEPTH_OF_FIELD: 0` and applying a separate background blur patch. The patch disables related blur; intended cinematic blur may also disappear. The precise internal parameter has not been independently identified. An alternative [experimental RenoDX effects package](https://github.com/decoded-brain/game-graphical-mods/blob/main/mods/detroit-become-human/README.md) replaces DOF through ReShade Full Add-On support. Its documentation does not establish compatibility with this Highball/MoltenVK installation, so it is not currently a demonstrated improvement.

## Use from the current source checkout

The v0.4.1-preview.1 release archives predate this optional tool. Use the current scripts together; older verification scripts reject any EXE change. No game files, backups or shaders are distributed.

Close Detroit first. Steam and Highball need not restart for this EXE-only change. Do not launch the game or run Steam verification/update during the operation.

```bash
# Preview without writing files:
python3 -B scripts/blur_workaround.py apply
# Only after explicitly choosing the workaround:
python3 -B scripts/blur_workaround.py apply --apply
python3 -B scripts/blur_workaround.py verify
./verify.sh
# Preview rollback, then restore the complete original EXE:
python3 -B scripts/blur_workaround.py rollback
python3 -B scripts/blur_workaround.py rollback --apply
```

The tool supports one reviewed Steam EXE version, matched by full SHA-256, unique pattern and offset. Unknown versions are refused. Only the owned private Detroit bottle is modified. A complete independently copied original is retained under Highball's private adapter state at `blur-workaround/original.exe`, then the EXE is atomically replaced. The original adapter transaction hash remains unchanged. Verification accepts only the exact known patched hash backed by a valid owned original; arbitrary changes are still rejected. Interrupted preparation can be retried.

At file offset `0x34e760`, `41` becomes `7F`. Disassembly shows a float constant changes from 16.0 to positive infinity. Steam updates or integrity verification may restore or replace the EXE. If a different version is installed, rollback refuses to overwrite it.

Nine synthetic transaction tests cover dry-run, application/verification/rollback/repeat, corrupted backups, unsupported or drifted EXEs, running-game rejection, unrecorded patches, interrupted publication and symlinks. These tests do not establish gameplay correctness.
