# Install, launch and restore

[简体中文](zh-CN/usage.md)

This guide uses the prebuilt library. **You do not need to compile MoltenVK or install the full Xcode application.**

**Tested: initial shader compilation passes the former 98% stop, and a later run with the audio fix and offline Metal cache was reported to play normally without repeating the long shader compilation. Long-session and audio-device reconnection testing remain open.**

## Already installed?

Use the normal **Detroit: Become Human** game page in Highball. Expand **Game settings** and check **Environment**. If it says `Games`, find **Also installed in Detroit Isolated** and click **Play there** when you are ready to start the game. Highball remembers this selection: subsequent presses of the main **Play** button use `Detroit Isolated`. No command launcher or reinstall is needed.

To add the new audio fix to an existing installation, use the [audio-only upgrade](../audio/README.md). If the environment is absent, follow the first-time steps below.

## Before you start

- Use **macOS 27, Highball 0.10.22 and x64-crossover26.3-r28** for the reviewed software baseline. Download [Highball 0.10.22](https://github.com/gauthierpiarrette/highball/releases/tag/v0.10.22), and check the source environment’s engine in its settings. The inspector rejects other engine revisions; do not replace an unrelated environment’s engine to make the check pass.
- Have the **Windows Steam edition** fully installed, with Windows Steam installed and signed in in the source Highball environment.
- The source environment needs the **x64 Visual C++ v14 runtime**, including `msvcp140.dll`, `mfc140.dll` and `vcruntime140.dll`. If absent, download the [Microsoft x64 redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) and use Highball’s **Run EXE** in that source environment to run its installer. The reviewed runtime was 14.51.36247.0; reference hashes are in `source-lock.json`. Microsoft DLLs are not included in this package. If already installed, leave them alone; the preflight checks presence and architecture.
- Allow space for **copies of the source environment, engine and entire game, plus at least 12 GiB spare**, often more than 75 GiB. The installer calculates required space.
- Confirm **Python 3.9 or later** (`python3 --version`) and `/usr/bin/lipo -version` work in Terminal. If macOS prompts for developer tools, complete the Command Line Tools installation. These tools check architecture; full Xcode is not required.

An “environment” (Bottle) is the Highball environment containing Windows Steam, for example `Games`.

## 1. Download

Open macOS Terminal, paste this entire block and press Return. A failed download or checksum stops the remaining steps inside the parentheses.

~~~bash
(
  set -e
  mkdir -p "$HOME/Downloads/highball-detroit-setup"
  cd "$HOME/Downloads/highball-detroit-setup"
  if [ -e highball-detroit-adapter-v0.3.0-preview.1 ]; then
    echo "This version is already extracted; use the existing folder."
    exit 1
  fi
  RELEASE="https://github.com/jason312928/highball-detroit-adapter/releases/download/v0.3.0-preview.1"
  ASSET="highball-detroit-adapter-v0.3.0-preview.1-macos-x86_64.tar.gz"
  curl --fail --location --output "$ASSET" "$RELEASE/$ASSET"
  curl --fail --location --output SHA256SUMS "$RELEASE/SHA256SUMS"
  awk -v asset="$ASSET" '$2 == asset { print; found=1 } END { if (!found) exit 1 }' \
    SHA256SUMS > selected.sha256
  shasum -a 256 -c selected.sha256
  tar -xzf "$ASSET"
  cd highball-detroit-adapter-v0.3.0-preview.1
  shasum -a 256 -c SHA256SUMS
)
~~~

Continue when every checksum entry says `OK`. If `highball-detroit-adapter-v0.3.0-preview.1` already exists, the block stops to avoid overwriting files. Use that existing download instead. The full archive contains the scripts and both libraries; no separate source download is needed.

Run the remaining steps in the **same Terminal window**, starting in the scripts directory:

~~~bash
cd "$HOME/Downloads/highball-detroit-setup/highball-detroit-adapter-v0.3.0-preview.1"
~~~

The downloaded `candidate.json` describes the library and its checksums. Its path is already filled in below; do not edit it.

## 2. Set the environment and game folder

You need two values:

1. **Source environment name:** find the Highball environment containing Windows Steam. The example uses `Games`; replace the quoted text if yours has another name.
2. **macOS game folder path:** in Finder, locate the `Detroit Become Human` folder containing `DetroitBecomeHuman.exe`. For an installation on the environment's C: drive, choose **Show the Windows drive** in Highball's environment menu, then locate Steam's `steamapps/common` folder. For an external disk, find its Steam library. Select the game folder and press **⌥⌘C** to copy its path.

Edit these two lines before running them. Keep double quotes to support spaces. Use a macOS path, not a Windows `C:\…` path.

~~~bash
SOURCE_BOTTLE="Games"
GAME_DIR="/paste/the/copied/game/folder/path/here"
~~~

Run the read-only checks:

~~~bash
python3 scripts/inspect_engine.py --source-bottle "$SOURCE_BOTTLE" &&
./install.sh --dry-run --source-bottle "$SOURCE_BOTTLE" \
  --game-dir "$GAME_DIR" --candidate-manifest "$PWD/candidate/candidate.json"
~~~

`DRY-RUN complete. No Highball or game files written.` means paths, library checksums and the engine fingerprint passed. **Nothing has been installed.** This step writes only logs and a local fingerprint in the download directory; it does not start the game.

Stop if any step reports `ERROR`. Consult the troubleshooting table before proceeding.

## 3. Install

Quit Windows Steam, the game, other Wine programs and Highball normally, then run:

~~~bash
./install.sh --apply --source-bottle "$SOURCE_BOTTLE" \
  --game-dir "$GAME_DIR" --candidate-manifest "$PWD/candidate/candidate.json" &&
./verify.sh &&
./audio/install.sh --dry-run &&
./audio/install.sh --apply &&
./audio/verify.sh
~~~

Copying the game may take time. `Private diagnostic engine and Bottle installed.`, followed by `Installed files verified:`, means installation and file verification completed. Repeating installation checks the existing result. Do not manually copy the dylib into a shared engine.

The new environment is **Detroit Isolated**, using **detroit-strict-003-r28**. The original game, cache, engine and EXE are preserved. Only the copied game's old cache is renamed for rebuilding on first launch. Other files in the source environment are copied too; saves do not automatically synchronize with the original environment. This copy is not a macOS security sandbox: Wine retains normal access to host files.

## 4. Prepare the Metal compiler

This step reproduces the reviewed setup **without installing full Xcode**. It downloads about 672 MiB from Apple and keeps roughly 2.1 GiB of private tools. It does not start a game or change the global developer-tool selection. Run once:

~~~bash
./prepare-metal.sh --dry-run &&
./prepare-metal.sh --apply &&
./prepare-metal.sh --verify
~~~

The pinned archive SHA-256, compiler SHA-256 and Apple code signature must pass. The archive key in `metal-toolchain-lock.json` is public Apple asset metadata, not an account credential. An existing verified toolchain is reused.

## 5. First game launch, then build the persistent cache

1. Open the normal **Detroit: Become Human** game page in Highball and expand **Game settings**.
2. If **Environment** is already `Detroit Isolated`, use the main **Play** button. Otherwise click **Play there** beside **Also installed in Detroit Isolated**. This starts the game and remembers the choice for future launches. Sign into the owning account in that Windows Steam instance if needed.
3. Let the first shader-compilation pass finish completely. Reaching 98% alone is not completion; wait until the menu appears. Check a scene, then quit the game normally and quit **the Windows Steam client in Detroit Isolated**. Do not stop other environments.
4. Return to the same extracted setup folder in Terminal and run:

~~~bash
./compile-cache.sh --dry-run 4 &&
./compile-cache.sh --apply 4
~~~

`4` is the number of concurrent compiler jobs; `8` was used in the reviewed cache build. This one-time step can take tens of minutes. Keep the Terminal open until `Done:` appears and the command returns successfully. **Do not start Detroit while this step runs.** It preserves the source files and atomically adds `.metallib` binaries, using the saved math/invariance options.

5. Open the normal Detroit game page in Highball and press **Play**. Its remembered environment should be `Detroit Isolated`. You do not need a `.command` launcher. Keep both the game’s `ShaderCache` and the private `.detroit-cache/msl` folder for subsequent launches. Do not delete either as routine maintenance.

The reference build produced 28,635 `.metallib` files, all accepted by native Metal; a second compiler run built zero and skipped all 28,635. The exact count can differ with scenes and settings. Later gameplay was reported normal without repeated long compilation. New shaders, a new GPU, changed software or graphics settings may require additional compilation; this does not promise zero compilation forever.

The original `Games` Steam client continues to use its original engine. For play from inside Steam, use the Windows Steam client in `Detroit Isolated`; changing one game’s Highball choice does not move other games or change the default environment.

If Steam says the game is not installed, check that you opened `Detroit Isolated` before downloading another copy. If the environment or launch item is missing, quit and reopen Highball; if still missing, run `./verify.sh`.

**Shader compilation must complete, the menu must respond and a scene must run correctly for the game test to pass.** `verify.sh` checks files; it cannot establish in-game results. The latest ordinary play report is positive, but it is not a long-session or every-scene acceptance test.

No graphics-setting edit or game-EXE patch is required by this workflow. The current reference retains depth of field and an unmodified EXE. If clipped highlights appear, try disabling HDR in the game’s graphics menu and compare the same scene. This is a diagnostic comparison, not a verified visual fix. Some scene interactions require holding the left mouse button while moving along the displayed gesture; menu clicks alone do not test that input path.

## 6. If the game stalls or crashes

Record the failing step, shader percentage and whether a game window appeared. In Highball's game details, **Show the last launch log** opens the latest launch log. Settings also provides **Show the logs folder**.

To inspect a log, select it in Finder, press **⌥⌘C** to copy its path and replace the quoted value below:

~~~bash
GAME_LOG="/paste/the/launch/log/path/here"
./verify.sh --game-log "$GAME_LOG"
~~~

- `private_library_load_observed: true`: the log contains independent MoltenVK loading evidence. `false` means no evidence was found; it does not establish that the wrong library loaded.
- `failure_line_count`: recognized error lines. Zero errors does not establish game success.

Script logs are in the download directory's `logs/` folder; full game logs stay local to Highball. Review paths and account details before sharing. The installer uploads nothing automatically.

## 7. Return to the original setup

Exit the test game and its Windows Steam instance, quit Wine programs and Highball, then run:

~~~bash
./prepare-metal.sh --rollback --dry-run &&
./prepare-metal.sh --rollback --apply &&
./audio/rollback.sh --dry-run &&
./audio/rollback.sh --apply &&
./rollback.sh --dry-run &&
./rollback.sh --apply
~~~

Reopen Highball and use the original environment and game launch item. Rollback moves the independent engine, environment, saves and diagnostics to `.detroit-adapter/archived/` inside Highball's data directory. **It retains files, so it does not immediately reclaim their disk space.** The command prints the archive path; keep it until saves are accounted for. Repeating rollback does not move files again.

If you closed Terminal, repeat the `cd` command at the end of step 1 before verification or rollback.

## Troubleshooting

| Message | Action |
|---|---|
| `python3: command not found` or developer-tools prompt | Install macOS Command Line Tools, reopen Terminal and check Python and lipo. |
| `Source bottle must be a real directory` | Check the original environment name, including spaces. This is not the game title. |
| `Only the x64-crossover26.3-r28 engine baseline has been reviewed` | Stop: this engine is outside the reviewed baseline. Do not change version identifiers to bypass this. |
| `Expected a regular file` naming the game EXE or `appmanifest_1222140.acf` | Check the Finder path. A complete Steam installation and its adjacent Steam manifest are required. |
| `Metal Toolchain unavailable` | Complete step 4, then retry cache compilation. |
| `Missing x64 Visual C++ runtime` | Install the Microsoft x64 runtime in the source environment before cloning. |
| `Close Highball and Wine/Windows programs` | Quit those programs normally and retry. The installer does not force them to close. |
| `Insufficient space` | Follow the space calculation, including the environment, engine, game copy and reserve. |
| `SHA-256 mismatch` or `FAILED` | Stop using the download and download it again. Do not bypass verification. |
| `Source engine differs` or `Existing fingerprint differs` | The source engine changed and requires review. Do not delete the fingerprint to bypass the check. |

A custom Highball data location is normally read from `HIGHBALL_HOME` or configuration. To specify it explicitly, pass the same `--highball-root "/actual/data/folder"` to the inspector, installation, verification and rollback commands.

## Custom compiler or existing installation

Already using an older adapter? Download and extract this release into a **new folder**, run `./verify.sh` and `./audio/verify.sh`, then follow steps 4 and 5. Do not reinstall or clear completed caches. If `audio/verify.sh` reports that the audio fix is absent, follow the [audio upgrade instructions](../audio/README.md) before testing.

The cache wrapper prefers the private pinned compiler. An existing Xcode compiler is a fallback, or select one explicitly with `METAL_TOOL="/absolute/path/to/metal"` on both cache commands. The reviewed 17A324 workflow is provided by `prepare-metal.sh`. `HIGHBALL_HOME` and Highball’s configured data location are detected; `HIGHBALL_ROOT="/actual/data/folder"` overrides the cache wrapper’s location. For tool preparation, pass `--highball-root "/actual/data/folder"` instead.

Tool rollback archives only the private tools under `.detroit-adapter/tools-archived-*`. Full adapter rollback retains game files, saves and caches in `.detroit-adapter/archived/`. Retained archives consume space until deliberately removed. No shared engine, system Vulkan installation or global audio setting is changed.
