#!/usr/bin/env python3
"""Prepare a pinned Apple compiler privately; never start Wine or change Xcode."""
import argparse
import contextlib
import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import uuid

import adapter

KIT = Path(__file__).resolve().parents[1]
COMPILER = Path("Metal.xctoolchain/usr/bin/metal")


def sha(path):
    return adapter.sha(path)


def run(args):
    result = subprocess.run([str(a) for a in args], text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"{args[0]} failed ({result.returncode}): {result.stderr}\n{result.stdout}")
    return result.stdout


def check_tools(path, lock):
    if path.is_symlink():
        raise ValueError("Refusing a symlinked tools directory")
    provenance = json.loads(adapter.regular(path / "provenance.json").read_text())
    if provenance.get("sha256") != lock["sha256"] or provenance.get("build") != lock["build"]:
        raise ValueError("Existing tools have different provenance; nothing overwritten")
    compiler = path / COMPILER
    if not compiler.resolve().is_relative_to(path.resolve()) or sha(compiler) != lock["compiler_sha256"]:
        raise ValueError("Apple compiler checksum mismatch")
    run(["/usr/bin/codesign", "--verify", "--strict", "-R=anchor apple", compiler])
    version = run([compiler, "--version"])
    if lock["compiler_version"] not in version:
        raise ValueError("Unexpected Apple compiler version")
    return compiler


def download_or_copy(archive, target, lock):
    if archive:
        shutil.copyfile(adapter.regular(archive), target)
    else:
        print("Downloading the pinned Metal Toolchain from Apple (about 672 MiB)...", flush=True)
        run(["/usr/bin/curl", "--fail", "--location", "--silent", "--show-error",
             "--retry", "2", "--connect-timeout", "20", "--output", target, lock["url"]])
    if target.stat().st_size != lock["bytes"] or sha(target) != lock["sha256"]:
        raise ValueError("Apple archive size/SHA-256 mismatch")


@contextlib.contextmanager
def mounted(image, mount):
    # Only this invocation's readonly image is attached or detached.
    run(["/usr/bin/hdiutil", "attach", "-readonly", "-nobrowse", "-mountpoint", mount, image])
    try:
        yield mount
    finally:
        run(["/usr/bin/hdiutil", "detach", mount])


def prepare(base, archive, lock):
    state = base / ".detroit-adapter"
    target = state / "tools"
    stage = state / ("tools-stage-" + uuid.uuid4().hex)
    if shutil.disk_usage(base).free < 5 * 1024**3:
        raise ValueError("Allow at least 5 GiB free for download, extraction and private tools")
    stage.mkdir(mode=0o700)
    work = Path(tempfile.mkdtemp(prefix="metal-work-", dir=state))
    try:
        package = work / "toolchain.aar"
        download_or_copy(archive, package, lock)
        raw = work / "toolchain.aa"
        run(["/usr/bin/aea", "decrypt", "-i", package, "-o", raw,
             "-key-value", "base64:" + lock["public_asset_decryption_key"]])
        empty, extracted = work / "empty", work / "extracted"
        empty.mkdir(); extracted.mkdir()
        run(["/usr/bin/aa", "patch", "-i", raw, "-src", empty, "-dst", extracted])
        images = list((extracted / "AssetData/Restore").glob("*.dmg"))
        if len(images) != 1:
            raise ValueError("Expected exactly one Apple toolchain image")
        with mounted(images[0], work / "mount") as mount:
            run(["/usr/bin/ditto", mount / "Metal.xctoolchain", stage / "Metal.xctoolchain"])
        adapter.save(stage / "provenance.json", lock)
        check_tools(stage, lock)
        # Refuse concurrent/user-created data, even if it appeared after preflight.
        if os.path.lexists(target):
            raise ValueError("Tools appeared during installation; refusing to replace them")
        os.rename(stage, target)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
        # Do not remove a still-mounted image after a detach error.
        if not os.path.ismount(work / "mount"):
            shutil.rmtree(work)
    print(f"Private Apple compiler ready: {target / COMPILER}", flush=True)


def execute(args):
    base = args.highball_root.expanduser().resolve()
    adapter.validate_base(base)
    state = adapter.state_dir(base)
    target = state / "tools"
    lock = json.loads((KIT / "metal-toolchain-lock.json").read_text())
    if args.verify:
        print(f"Verified: {check_tools(target, lock)}")
        return 0
    if os.path.lexists(target):
        check_tools(target, lock)
        if not args.rollback:
            print("Already prepared and verified; no files changed.")
            return 0
    elif args.rollback:
        print("Already rolled back; no tools to move.")
        return 0
    if not args.apply:
        print("DRY-RUN: archive private tools." if args.rollback else
              f"DRY-RUN: download Apple build {lock['build']} ({lock['bytes']} bytes), "
              "verify SHA-256/signature, prepare a private compiler. No download or installation performed.")
        return 0
    with adapter.locked(base):
        # A separate lock protects this component while retaining engine transaction state.
        with (state / "metal-tools.lock").open("a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if args.rollback:
                check_tools(target, lock)
                archive = state / ("tools-archived-" + uuid.uuid4().hex)
                os.rename(target, archive)
                print(f"Tools retained in: {archive}")
            elif target.exists():
                check_tools(target, lock)
                print("Already prepared and verified.")
            else:
                prepare(base, args.archive, lock)
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--highball-root", type=Path, default=adapter.default_highball_root())
    action = p.add_mutually_exclusive_group()
    action.add_argument("--verify", action="store_true")
    action.add_argument("--rollback", action="store_true")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    p.add_argument("--archive", type=Path, help="Use a local archive with the same pinned SHA-256")
    args = p.parse_args()
    if args.archive:
        args.archive = args.archive.expanduser().resolve()
    def interrupted(_signum, _frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    try:
        return execute(args)
    except KeyboardInterrupt:
        print("Interrupted; incomplete private stage removed.", file=sys.stderr)
        return 130
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
