#!/usr/bin/env python3
"""Install the reviewed Detroit-only XAudio2 fix. Dry-run by default."""

import argparse
import fcntl
import hashlib
import json
import os
import shutil
import struct
import subprocess
from pathlib import Path

KIT = Path(__file__).resolve().parent
OLD = "ac38c792dfe1abfb5b2a94eebecc91caa05126e012e0e1deef3567cd1c897a7b"
NEW = "a19d4e199aaf70bb2990a51bf6fda9c4466612c9e2306365ff29f7d8983fd2cb"
RELS = [
    "engines/detroit-strict-003-r28/engine/lib/wine/x86_64-windows/xaudio2_8.dll",
    "bottles/Detroit Isolated/drive_c/windows/system32/xaudio2_8.dll",
]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def regular(p):
    if not p.is_file() or p.is_symlink():
        raise ValueError("Expected regular file: " + str(p))
    return p


def read(p):
    return json.loads(regular(p).read_text())


def save(p, obj):
    tmp = p.with_suffix(".tmp")
    with tmp.open("w") as f:
        json.dump(obj, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)


def copy_atomic(src, dst):
    tmp = dst.with_name("." + dst.name + ".audiofix-tmp")
    if tmp.exists() or tmp.is_symlink():
        raise ValueError("Temporary path conflict: " + str(tmp))
    try:
        shutil.copy2(src, tmp)
        os.replace(tmp, dst)
    finally:
        if tmp.exists():
            tmp.unlink()


def check(base):
    journal = read(base / ".detroit-adapter/transaction.json")
    if journal["status"] != "installed":
        raise ValueError("Install the Detroit isolated environment first")
    for rel in ["engines/detroit-strict-003-r28", "bottles/Detroit Isolated"]:
        p = base / rel
        if (
            p.is_symlink()
            or read(p / ".detroit-adapter-owner.json")["token"] != journal["token"]
        ):
            raise ValueError("Private environment ownership mismatch")
    settings = read(base / "bottles/Detroit Isolated/bottle.json")
    if settings["engineID"] != "detroit-strict-003-r28":
        raise ValueError("Unexpected private engine")
    return journal["token"]


def quiet(base):
    rows = subprocess.run(
        ["/bin/ps", "-axo", "comm="],
        text=True,
        capture_output=True,
        errors="replace",
        check=True,
    ).stdout.splitlines()
    names = [
        str(base / "bottles/Detroit Isolated"),
        str(base / "engines/detroit-strict-003-r28"),
    ]
    if any(
        "detroitbecomehuman.exe" in s.lower() or any(n in s for n in names)
        for s in rows
    ):
        raise ValueError(
            "Exit Detroit and private Wine programs before installation/rollback; nothing was stopped"
        )


def candidate():
    p = regular(KIT / "xaudio2_8.dll")
    b = p.read_bytes()
    if sha(p) != NEW:
        raise ValueError("Candidate checksum mismatch")
    pe = struct.unpack_from("<I", b, 0x3C)[0]
    if (
        b[:2] != b"MZ"
        or b[pe : pe + 4] != b"PE\0\0"
        or struct.unpack_from("<H", b, pe + 4)[0] != 0x8664
    ):
        raise ValueError("Expected x86_64 PE DLL")
    if b"Wine builtin DLL" not in b or b"HB_DETROIT_AUDIO_V1" not in b:
        raise ValueError("Candidate identity missing")
    return p


def restore(base, state, j):
    if j["private_token"] != check(base):
        raise ValueError("Ownership changed")
    entries = []
    for i, rel in enumerate(RELS):
        dst = regular(base / rel)
        backup = regular(state / ("backup-" + str(i) + ".dll"))
        if sha(backup) != OLD:
            raise ValueError("Backup checksum mismatch")
        current = sha(dst)
        if current not in [OLD, NEW]:
            raise ValueError(
                "Library changed after installation; refusing to overwrite " + str(dst)
            )
        entries.append((dst, backup, current))
    changed = []
    try:
        for dst, backup, current in entries:
            if current == NEW:
                copy_atomic(backup, dst)
                changed.append(dst)
    except BaseException:
        for dst in reversed(changed):
            copy_atomic(candidate(), dst)
        raise
    j["status"] = "rolled-back"
    save(state / "transaction.json", j)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("operation", choices=["install", "verify", "rollback"])
    p.add_argument(
        "--highball-root",
        type=Path,
        default=Path.home() / "Library/Application Support/Highball",
    )
    p.add_argument(
        "--if-installed",
        action="store_true",
        help="Verification only: permit an absent or rolled-back audio fix",
    )
    g = p.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = p.parse_args()
    base = a.highball_root.expanduser().resolve()
    token = check(base)
    routing_state = base / ".detroit-adapter/audio-routing-v2/transaction.json"
    if routing_state.exists() and read(routing_state)["status"] in ["installed", "installing"]:
        import routingfix
        if a.operation == "rollback":
            raise ValueError("Roll back audio routing first with audio/rollback-routing.sh --apply")
        routingfix.verify(base, read(routing_state))
        print("Audio routing v2 is installed and verified; v1 remains its rollback baseline.")
        return
    lib = candidate()
    state = base / ".detroit-adapter/audio-v1"
    if state.is_symlink():
        raise ValueError("Unsafe state directory")
    path = state / "transaction.json"
    j = read(path) if path.exists() else None
    if a.operation == "install" and j and j["status"] == "installing":
        if j["private_token"] != token:
            raise ValueError("Interrupted installation ownership changed")
        for i, rel in enumerate(RELS):
            if (
                sha(regular(base / rel)) not in [OLD, NEW]
                or sha(regular(state / ("backup-" + str(i) + ".dll"))) != OLD
            ):
                raise ValueError("Interrupted state has conflicting files")
        if not a.apply:
            print(
                "DRY-RUN: interrupted installation is recoverable; --apply will restore backups before reinstalling."
            )
            return
        quiet(base)
        with (state / "lock").open("a") as recovery_lock:
            fcntl.flock(recovery_lock.fileno(), fcntl.LOCK_EX)
            j = read(path)
            restore(base, state, j)
        print("Recovered interrupted audio installation.")
    if a.operation == "verify":
        if a.if_installed and (not j or j["status"] == "rolled-back"):
            print("No active audio fix; verification skipped.")
            return
        if not j or j["status"] != "installed" or j["private_token"] != token:
            raise ValueError("Audio fix is not installed")
        for rel in RELS:
            if sha(regular(base / rel)) != NEW:
                raise ValueError("Installed audio library checksum mismatch")
        print(
            "Audio fix verified: both private x86_64 DLLs match. Gameplay recovery is not established by this check."
        )
        return
    if a.operation == "rollback":
        if not j or j["status"] == "rolled-back":
            print("Audio rollback already complete.")
            return
        if not a.apply:
            print(
                "DRY-RUN: would restore the two original private audio libraries; game saves untouched."
            )
            return
    else:
        if j and j["status"] == "installed":
            for rel in RELS:
                if sha(regular(base / rel)) != NEW:
                    raise ValueError("Existing audio install differs")
            print("Audio fix already installed; no files changed.")
            return
        for rel in RELS:
            if sha(regular(base / rel)) != OLD:
                raise ValueError(
                    "Unexpected original audio library: " + str(base / rel)
                )
        if not a.apply:
            print(
                "DRY-RUN passed: x86_64 candidate and both original library hashes verified. Would replace only two Detroit-private DLLs."
            )
            return
    quiet(base)
    state.mkdir(parents=True, exist_ok=True)
    lock = state / "lock"
    if lock.is_symlink():
        raise ValueError("Unsafe lock")
    with lock.open("a") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        j = read(path) if path.exists() else None
        if a.operation == "rollback":
            restore(base, state, j)
            print("Original Detroit-private audio libraries restored.")
            return
        if j and j["status"] == "installing":
            restore(base, state, j)
        for rel in RELS:
            if sha(regular(base / rel)) != OLD:
                raise ValueError("Concurrent library change")
        for i, rel in enumerate(RELS):
            b = state / ("backup-" + str(i) + ".dll")
            if b.exists():
                if sha(regular(b)) != OLD:
                    raise ValueError("Existing backup differs")
            else:
                shutil.copy2(regular(base / rel), b)
        j = {
            "status": "installing",
            "private_token": token,
            "old_sha256": OLD,
            "new_sha256": NEW,
            "paths": RELS,
        }
        save(path, j)
        try:
            for rel in RELS:
                copy_atomic(lib, base / rel)
            for rel in RELS:
                if sha(regular(base / rel)) != NEW:
                    raise ValueError("Installed checksum mismatch")
            j["status"] = "installed"
            save(path, j)
        except BaseException:
            restore(base, state, j)
            raise
        print(
            "Detroit-private XAudio2 error-propagation fix installed. Original DLLs backed up. No game was launched."
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", e)
        raise SystemExit(1)
