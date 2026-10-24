# Usage

[简体中文](zh-CN/usage.md)

## Prerequisites

The reviewed engine baseline is x64-crossover26.3-r28. The runtime library must contain an x86_64 slice. Builds for other engine revisions require a separate compatibility review.

Record the local engine identity before installation planning:

~~~bash
python3 scripts/inspect_engine.py --source-bottle Games
~~~

This reads the engine and writes only engine-lock.local.json. The file contains engine identity and hashes, is ignored by Git, and is not a compatibility certificate. A changed fingerprint requires review.

## Install

Close Highball and Wine programs. The installer never stops them automatically.

~~~bash
./install.sh --dry-run --game-dir "/path/to/steamapps/common/Detroit Become Human" \
  --candidate-manifest "$PWD/build/candidate.json"
./install.sh --apply --game-dir "/path/to/steamapps/common/Detroit Become Human" \
  --candidate-manifest "$PWD/build/candidate.json"
./verify.sh
~~~

For the prerelease binary archive, replace build/candidate.json with the extracted candidate.json path.

The new engine is detroit-strict-003-r28; the new Bottle is Detroit Isolated. Engine files, the source Bottle and the complete game are copied. The original game cache is preserved; the copied cache is renamed before the first run. Installation does not launch Wine or modify the game executable, depth-of-field setting, shared engine or system Vulkan installation.

Paths containing spaces are supported. Use --highball-root and --source-bottle for a non-default layout. The game directory must have a corresponding Steam appmanifest_1222140.acf.

Installation is transactional and repeatable. The local journal lives under Highball/.detroit-adapter. Ordinary failures remove only new transaction-owned paths; interrupted operations are recovered on a subsequent run.

## Run and collect evidence

In Highball, select Detroit Isolated and its Detroit (isolated Steam) pin. Confirm the actual loaded dylib before assessing shader progress. The private configuration enables library-load logging and shader dumps.

~~~bash
./verify.sh --game-log "/path/to/run.log"
~~~

This checks load evidence and recognizable failures. It does not infer completion of shader compilation, menu interaction or scene rendering. Wine retains normal access to host files; the copied environment is not an OS sandbox.

After shader compilation finishes and Wine exits, compile the private Metal cache with:

~~~bash
./compile-cache.sh --dry-run 4
./compile-cache.sh --apply 4
~~~

Offline compilation requires the Metal Toolchain. Routine launches should retain the completed game cache. There is no executable patch or automatic depth-of-field change.

## Rollback

~~~bash
./rollback.sh --dry-run
./rollback.sh --apply
~~~

Only the transaction-owned engine and Bottle are moved into Highball/.detroit-adapter/archived. Saves and diagnostics are retained. Original game files and the source engine remain in place.
