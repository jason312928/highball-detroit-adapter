#!/usr/bin/env python3
"""Opt-in, version-locked background blur workaround; dry-run by default."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import adapter

ORIGINAL = "ecf52321921387e683904e089082d76b973326fc093af14e524056715519c1cf"
PATCHED = "999804b51c1fcc12e38056495139d67f076658b9b4656068c9cfdb29208e69bf"
OFFSET = 3467104
PATTERN = bytes.fromhex("41 c7 83 40 01 00 00 31 00 00")
GAME = "drive_c/DetroitSteamLibrary/steamapps/common/Detroit Become Human/DetroitBecomeHuman.exe"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def transformed(data):
    if digest(data) != ORIGINAL or data.count(PATTERN) != 1 or data[OFFSET:OFFSET + len(PATTERN)] != PATTERN:
        raise ValueError("Unsupported or modified EXE; no pattern-only patching is allowed.")
    result = bytearray(data)
    result[OFFSET] = 0x7f
    result = bytes(result)
    if digest(result) != PATCHED:
        raise ValueError("Unexpected patched EXE checksum.")
    return result


def paths(base):
    adapter.validate_base(base)
    journal = adapter.read(adapter.regular(adapter.state_dir(base) / "transaction.json"))
    engine, bottle = adapter.targets(base)
    if journal.get("status") != "installed" or not all(adapter.owned(p, journal["token"]) for p in (engine, bottle)):
        raise ValueError("A complete owned Detroit installation is required.")
    exe = adapter.regular(bottle / GAME)
    if not exe.resolve().is_relative_to(bottle.resolve()):
        raise ValueError("Game path escapes the private Detroit bottle.")
    directory = adapter.state_dir(base) / "blur-workaround"
    if directory.is_symlink():
        raise ValueError("Backup directory must not be a symlink.")
    return exe, directory, journal


def check_backup(directory, journal):
    record = adapter.read(adapter.regular(directory / "transaction.json"))
    if (record.get("token"), record.get("original_sha256"), record.get("patched_sha256")) != (journal["token"], ORIGINAL, PATCHED):
        raise ValueError("Blur workaround ownership or checksum record mismatch.")
    backup = adapter.regular(directory / "original.exe")
    data = backup.read_bytes()
    if digest(data) != ORIGINAL or digest(transformed(data)) != PATCHED:
        raise ValueError("Original EXE backup is damaged.")
    return data


def verify_executable(base, exe, journal):
    current = adapter.sha(exe)
    if current == journal["source_exe_sha256"]:
        return "original"
    if current != PATCHED or journal["source_exe_sha256"] != ORIGINAL:
        raise ValueError("Private game EXE changed; investigate before playing.")
    directory = adapter.state_dir(base) / "blur-workaround"
    if directory.is_symlink():
        raise ValueError("Unsafe blur workaround directory.")
    check_backup(directory, journal)
    return "known-background-blur-workaround"


def game_stopped():
    rows = subprocess.check_output(["/bin/ps", "-axo", "comm="], text=True)
    if any(row.strip().lower().endswith("detroitbecomehuman.exe") for row in rows.splitlines()):
        raise ValueError("Close Detroit before modifying its EXE; nothing was stopped.")


def atomic_exe(exe, data, expected):
    fd, name = tempfile.mkstemp(prefix=".blur-workaround-", dir=exe.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        shutil.copystat(exe, name)
        if adapter.sha(exe) != expected:
            raise ValueError("Game EXE changed during preparation; refusing replacement.")
        game_stopped()
        os.replace(name, exe)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def operate(base, action, apply=False):
    exe, directory, journal = paths(base)
    current = adapter.sha(exe)
    if action == "verify":
        adapter.log("EXE state: " + verify_executable(base, exe, journal))
        return
    if action == "rollback":
        if current == ORIGINAL:
            adapter.log("Original EXE already present; nothing changed.")
            return
        if current != PATCHED:
            raise ValueError("EXE changed since patching; refusing rollback over an unknown version.")
        data = check_backup(directory, journal)
    else:
        if current == PATCHED:
            verify_executable(base, exe, journal)
            adapter.log("Known blur workaround already present; nothing changed.")
            return
        if journal["source_exe_sha256"] != ORIGINAL:
            raise ValueError("This Steam EXE version is not supported.")
        data = transformed(exe.read_bytes())
    adapter.log(f"{action}: private Detroit EXE only; one-byte workaround; cinematic blur may be removed.")
    if not apply:
        adapter.log("DRY-RUN: no backup or game file was written. Use --apply to execute.")
        return
    game_stopped()
    with adapter.locked(base):
        # Revalidate after acquiring the shared installer lock.
        if adapter.sha(exe) != current:
            raise ValueError("EXE changed while acquiring lock.")
        directory.mkdir(mode=0o700, exist_ok=True)
        if action == "apply":
            backup = directory / "original.exe"
            if os.path.lexists(backup):
                if adapter.sha(adapter.regular(backup)) != ORIGINAL:
                    raise ValueError("Existing backup differs; refusing to overwrite it.")
            else:
                with backup.open("xb") as f:
                    f.write(exe.read_bytes())
                    f.flush()
                    os.fsync(f.fileno())
                shutil.copystat(exe, backup)
            record = {"token": journal["token"], "original_sha256": ORIGINAL, "patched_sha256": PATCHED, "offset": OFFSET, "status": "prepared"}
            if os.path.lexists(directory / "transaction.json"):
                check_backup(directory, journal)
            adapter.save(directory / "transaction.json", record)
            check_backup(directory, journal)
        else:
            data = check_backup(directory, journal)
            record = adapter.read(directory / "transaction.json")
        atomic_exe(exe, data, current)
        if adapter.sha(exe) != (PATCHED if action == "apply" else ORIGINAL):
            raise ValueError("Final EXE verification failed; backup retained.")
        record["status"] = "applied" if action == "apply" else "rolled-back"
        adapter.save(directory / "transaction.json", record)
        adapter.log("Verified: " + record["status"] + "; original backup retained.")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("apply", "rollback", "verify"))
    p.add_argument("--apply", action="store_true", help="Authorize the selected mutation; otherwise dry-run")
    p.add_argument("--highball-root", type=Path, default=adapter.default_highball_root())
    a = p.parse_args()
    operate(a.highball_root.expanduser().resolve(), a.action, a.apply)


if __name__ == "__main__":
    main()
