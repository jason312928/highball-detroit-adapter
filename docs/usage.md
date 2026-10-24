# Install, launch and restore

[简体中文](zh-CN/usage.md)

This guide uses the prebuilt library. **You do not need to compile MoltenVK or install the full Xcode application.**

**This is a diagnostic build. It can install an independent test environment, but completion of Detroit: Become Human's first shader compilation, the main menu and gameplay remain unverified. Installation success does not mean the game is fixed.**

## Already installed?

Open Highball. If **Detroit Isolated** is in the environment list, open it and select **Detroit (isolated Steam)**. Launching from the original environment may still use its original library. You do not need to download, build or install again.

If that environment is absent, follow the first-time steps below.

## Before you start

- The reviewed combination is **Highball 0.10.22 / x64-crossover26.3-r28**. The inspector rejects other engine revisions.
- Have the **Windows Steam edition** fully installed, with Windows Steam installed in the source Highball environment.
- Allow space for **copies of the source environment, engine and entire game, plus at least 5 GiB spare**, typically more than 64 GiB. The installer calculates required space.
- Confirm `python3 --version` and `/usr/bin/lipo -version` work in Terminal. If macOS prompts for developer tools, complete the Command Line Tools installation. These tools check architecture; full Xcode is not required.

An “environment” (Bottle) is the Highball environment containing Windows Steam, for example `Games`.

## 1. Download

Open macOS Terminal, paste this entire block and press Return. A failed download or checksum stops the remaining steps inside the parentheses.

~~~bash
(
  set -e
  mkdir -p "$HOME/Downloads/highball-detroit-setup"
  cd "$HOME/Downloads/highball-detroit-setup"
  if [ -e highball-detroit-adapter-main ]; then
    echo "Download folder already exists; use it or choose another setup directory."
    exit 1
  fi
  curl --fail --location --output source.zip \
    https://github.com/jason312928/highball-detroit-adapter/archive/refs/heads/main.zip
  unzip -q source.zip
  cd highball-detroit-adapter-main
  mkdir -p release/candidate
  cd release
  RELEASE="https://github.com/jason312928/highball-detroit-adapter/releases/download/v0.1.0-diagnostic.1"
  ASSET="highball-detroit-moltenvk-v0.1.0-diagnostic.1-macos-x86_64.tar.gz"
  curl --fail --location --output "$ASSET" "$RELEASE/$ASSET"
  curl --fail --location --output 0001-strict-interfaces-and-pinned-spirv.patch \
    "$RELEASE/0001-strict-interfaces-and-pinned-spirv.patch"
  curl --fail --location --output SHA256SUMS "$RELEASE/SHA256SUMS"
  shasum -a 256 -c SHA256SUMS
  tar -xzf "$ASSET" -C candidate
  cd candidate
  shasum -a 256 -c SHA256SUMS
)
~~~

Continue when every checksum entry says `OK`. If `highball-detroit-adapter-main` already exists, the block stops to avoid overwriting files. Use that existing download instead.

Run the remaining steps in the **same Terminal window**, starting in the scripts directory:

~~~bash
cd "$HOME/Downloads/highball-detroit-setup/highball-detroit-adapter-main"
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
  --game-dir "$GAME_DIR" --candidate-manifest "$PWD/release/candidate/candidate.json"
~~~

`DRY-RUN complete. No Highball or game files written.` means paths, library checksums and the engine fingerprint passed. **Nothing has been installed.** This step writes only logs and a local fingerprint in the download directory; it does not start the game.

Stop if any step reports `ERROR`. Consult the troubleshooting table before proceeding.

## 3. Install

Quit Windows Steam, the game, other Wine programs and Highball normally, then run:

~~~bash
./install.sh --apply --source-bottle "$SOURCE_BOTTLE" \
  --game-dir "$GAME_DIR" --candidate-manifest "$PWD/release/candidate/candidate.json" &&
./verify.sh
~~~

Copying the game may take time. `Private diagnostic engine and Bottle installed.`, followed by `Installed files verified:`, means installation and file verification completed. Repeating installation checks the existing result. Do not manually copy the dylib into a shared engine.

The new environment is **Detroit Isolated**, using **detroit-strict-003-r28**. The original game, cache, engine and EXE are preserved. Only the copied game's old cache is renamed for rebuilding on first launch. Other files in the source environment are copied too; saves do not automatically synchronize with the original environment. This copy is not a macOS security sandbox: Wine retains normal access to host files.

## 4. Launch the game

1. Open Highball and select **Detroit Isolated**.
2. Select **Detroit (isolated Steam)**. Sign into the owning account in this Windows Steam instance if needed.
3. Wait for first-time shader compilation and record whether it passes 98% and finishes.
4. If it finishes, check that the main menu responds, then start a scene and check for visual errors or crashes.

If Steam says the game is not installed, check that you opened `Detroit Isolated` before downloading another copy. If the environment or launch item is missing, quit and reopen Highball; if still missing, run `./verify.sh`.

**Shader compilation must complete, the menu must respond and a scene must run correctly for the game test to pass.** `verify.sh` checks files; it cannot establish these in-game results. The project has not completed this acceptance test yet.

## 5. If the game stalls or crashes

Record the failing step, shader percentage and whether a game window appeared. In Highball's game details, **Show the last launch log** opens the latest launch log. Settings also provides **Show the logs folder**.

To inspect a log, select it in Finder, press **⌥⌘C** to copy its path and replace the quoted value below:

~~~bash
GAME_LOG="/paste/the/launch/log/path/here"
./verify.sh --game-log "$GAME_LOG"
~~~

- `private_library_load_observed: true`: the log contains independent MoltenVK loading evidence. `false` means no evidence was found; it does not establish that the wrong library loaded.
- `failure_line_count`: recognized error lines. Zero errors does not establish game success.

Script logs are in the download directory's `logs/` folder; full game logs stay local to Highball. Review paths and account details before sharing. The installer uploads nothing automatically.

## 6. Return to the original setup

Exit the test game and its Windows Steam instance, quit Wine programs and Highball, then run:

~~~bash
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
| `Close Highball and Wine/Windows programs` | Quit those programs normally and retry. The installer does not force them to close. |
| `Insufficient space` | Follow the space calculation, including the environment, engine, game copy and reserve. |
| `SHA-256 mismatch` or `FAILED` | Stop using the download and download it again. Do not bypass verification. |
| `Source engine differs` or `Existing fingerprint differs` | The source engine changed and requires review. Do not delete the fingerprint to bypass the check. |

A custom Highball data location is normally read from `HIGHBALL_HOME` or configuration. To specify it explicitly, pass the same `--highball-root "/actual/data/folder"` to the inspector, installation, verification and rollback commands.

## Optional: offline Metal cache

**This is not required to install or first launch the game.** Use it only after the game's own shader compilation completes, Wine exits and the Metal Toolchain is installed:

~~~bash
./compile-cache.sh --dry-run 4 &&
./compile-cache.sh --apply 4
~~~

`4` is the number of parallel jobs. The offline cache workflow has not completed runtime acceptance. Skip it if the `metal` compiler is unavailable; retain the game's completed cache. For custom data locations, also set `HIGHBALL_ROOT="/actual/data/folder"` for both commands. Source compilation is covered separately in [Build](build.md).
