#!/usr/bin/env python3
"""Install the Detroit-only default-output routing candidate; dry-run by default."""

import argparse
import ctypes
import fcntl
import subprocess
import sys
from pathlib import Path
import shutil
import struct

import audiofix

KIT = Path(__file__).resolve().parent / "routing"
KEY = "HB_DETROIT_AUDIO_FOLLOW_DEFAULT"
SETTINGS = "bottles/Detroit Isolated/bottle.json"
STATE = ".detroit-adapter/audio-routing-v2"
DIRS = (
    "engines/detroit-strict-003-r28/engine/lib/wine/x86_64-windows",
    "bottles/Detroit Isolated/drive_c/windows/system32",
)


def require_closed_highball():
    rows = subprocess.run(["/bin/ps", "-axo", "comm="], text=True,
                          capture_output=True, check=True).stdout.splitlines()
    if any(row.strip().endswith("/Highball") for row in rows):
        raise ValueError("Quit Highball before changing audio files/settings, so its next launch reloads the bottle configuration")


def live_environments(base):
    """Read only matching private clients; never print or save their full environment."""
    if sys.platform != "darwin":
        return []
    prefix = str(base / "bottles/Detroit Isolated") + "/"
    rows = subprocess.run(["/bin/ps", "-axo", "pid=,comm="], text=True,
                          capture_output=True, check=True).stdout.splitlines()
    system = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
    result = []
    for row in rows:
        parts = row.strip().split(None, 1)
        if len(parts) != 2:
            continue
        pid, command = parts
        if not command.startswith(prefix) or Path(command).name.lower() not in ["steam.exe", "detroitbecomehuman.exe"]:
            continue
        mib = (ctypes.c_int * 3)(1, 49, int(pid))  # CTL_KERN, KERN_PROCARGS2
        size = ctypes.c_size_t()
        if system.sysctl(mib, 3, None, ctypes.byref(size), None, 0) != 0:
            raise ValueError("Cannot inspect the running private client; runtime configuration remains unverified")
        data = ctypes.create_string_buffer(size.value)
        if system.sysctl(mib, 3, data, ctypes.byref(size), None, 0) != 0 or size.value < 4:
            raise ValueError("Private client exited during verification; retry")
        argc = struct.unpack_from("i", data.raw)[0]
        strings = [s.decode(errors="replace") for s in data.raw[4:size.value].split(b"\0") if s]
        env = dict(s.split("=", 1) for s in strings[1 + argc:] if "=" in s)
        result.append((Path(command).name, env.get(KEY)))
    return result


def manifest():
    value = audiofix.read(KIT / "manifest.json")
    if set(value["files"]) != {"xaudio2_8.dll", "mmdevapi.dll"}:
        raise ValueError("Unexpected routing bundle")
    for name, spec in value["files"].items():
        p = audiofix.regular(KIT / name)
        data = p.read_bytes()
        if audiofix.sha(p) != spec["sha256"]:
            raise ValueError("Routing candidate checksum mismatch: " + name)
        if len(data) < 64 or data[:2] != b"MZ":
            raise ValueError("Invalid PE candidate")
        offset = struct.unpack_from("<I", data, 60)[0]
        if data[offset:offset + 6] != b"PE\0\0\x64\x86":
            raise ValueError("Expected x86_64 candidate")
        if b"Wine builtin DLL" not in data or b"HB_DETROIT_AUDIO_" not in data:
            raise ValueError("Routing candidate identity missing")
    return value


def state_dir(base):
    state = base / STATE
    for p in [base / ".detroit-adapter", state]:
        if p.is_symlink():
            raise ValueError("Unsafe routing state")
    return state


def env_value(base):
    env = audiofix.read(base / SETTINGS).get("environment", {})
    return {"present": KEY in env, "value": env.get(KEY)}


def set_env(base, expected, replacement):
    settings = audiofix.read(base / SETTINGS)
    env = settings.setdefault("environment", {})
    if {"present": KEY in env, "value": env.get(KEY)} != expected:
        raise ValueError("Routing setting changed concurrently")
    if replacement["present"]:
        env[KEY] = replacement["value"]
    else:
        env.pop(KEY, None)
    audiofix.save(base / SETTINGS, settings)


ENABLED = {"present": True, "value": "1"}


def inspect(base, bundle):
    entries = []
    for directory in DIRS:
        for name, spec in bundle["files"].items():
            rel = directory + "/" + name
            current = audiofix.sha(audiofix.regular(base / rel))
            if current not in spec["accepted_previous_sha256"]:
                raise ValueError("Unreviewed installed DLL: " + rel)
            entries.append({"path": rel, "name": name, "before": current,
                            "after": spec["sha256"], "backup": str(len(entries)) + ".dll"})
    return entries


def verify(base, journal):
    validate_journal(journal)
    if journal["private_token"] != audiofix.check(base) or journal["status"] != "installed":
        raise ValueError("Routing fix is not installed for this environment")
    for entry in journal["entries"]:
        if audiofix.sha(audiofix.regular(base / entry["path"])) != entry["after"]:
            raise ValueError("Installed routing DLL differs")
    if env_value(base) != ENABLED:
        raise ValueError("Default-output following is disabled")
    for program, value in live_environments(base):
        if value != "1":
            raise ValueError(f"{program} is running without {KEY}=1; close the game and private Steam, reload Highball settings, then relaunch")


def restore(base, state, journal):
    validate_journal(journal)
    if journal["private_token"] != audiofix.check(base):
        raise ValueError("Routing ownership changed")
    for entry in journal["entries"]:
        if audiofix.sha(audiofix.regular(state / entry["backup"])) != entry["before"]:
            raise ValueError("Routing backup differs")
        if audiofix.sha(audiofix.regular(base / entry["path"])) not in [entry["before"], entry["after"]]:
            raise ValueError("Routing DLL changed after installation")
    current = env_value(base)
    if current not in [ENABLED, journal["environment_before"]]:
        raise ValueError("Routing setting changed after installation")
    for entry in journal["entries"]:
        audiofix.copy_atomic(state / entry["backup"], base / entry["path"])
    if current == ENABLED:
        set_env(base, ENABLED, journal["environment_before"])
    journal["status"] = "rolled-back"
    audiofix.save(state / "transaction.json", journal)


def validate_journal(journal):
    bundle = manifest()
    expected = [(directory + "/" + name, name, spec)
                for directory in DIRS for name, spec in bundle["files"].items()]
    if len(journal["entries"]) != len(expected):
        raise ValueError("Unexpected routing journal entries")
    for index, (entry, (path, name, spec)) in enumerate(zip(journal["entries"], expected)):
        if (entry["path"] != path or entry["name"] != name
                or entry["backup"] != str(index) + ".dll"
                or entry["after"] != spec["sha256"]
                or entry["before"] not in spec["accepted_previous_sha256"]):
            raise ValueError("Routing journal does not match the reviewed bundle")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["install", "verify", "rollback"])
    parser.add_argument("--highball-root", type=Path,
                        default=Path.home() / "Library/Application Support/Highball")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    base = args.highball_root.expanduser().resolve()
    token = audiofix.check(base)
    bundle = manifest()
    state = state_dir(base)
    path = state / "transaction.json"
    journal = audiofix.read(path) if path.exists() else None
    if args.operation == "verify":
        if journal is None:
            raise ValueError("Routing fix has not been installed")
        verify(base, journal)
        print("Routing candidate verified: four private DLLs and default-output setting match.")
        return
    if args.operation == "rollback" and (not journal or journal["status"] == "rolled-back"):
        print("Routing rollback already complete.")
        return
    if args.operation == "install" and journal and journal["status"] == "installed":
        verify(base, journal)
        print("Routing candidate already installed; no files changed.")
        return
    if args.operation == "install" and not (journal and journal["status"] == "installing"):
        inspect(base, bundle)
    if not args.apply:
        print("DRY-RUN: would " + ("restore routing backups" if args.operation == "rollback" else
              "install two audio DLLs in the private engine and bottle, with backups; enable default-output following") + ".")
        return
    audiofix.quiet(base)
    require_closed_highball()
    state.mkdir(parents=True, exist_ok=True)
    lock = state / "lock"
    if lock.is_symlink():
        raise ValueError("Unsafe routing lock")
    with lock.open("a") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        journal = audiofix.read(path) if path.exists() else None
        if args.operation == "rollback":
            restore(base, state, journal)
            print("Routing backups restored; unrelated bottle settings preserved.")
            return
        if journal and journal["status"] == "installed":
            verify(base, journal)
            return
        if journal and journal["status"] == "installing":
            restore(base, state, journal)
        entries = inspect(base, bundle)
        for entry in entries:
            backup = state / entry["backup"]
            if backup.exists():
                if audiofix.sha(audiofix.regular(backup)) != entry["before"]:
                    raise ValueError("Existing routing backup differs")
            else:
                shutil.copy2(base / entry["path"], backup)
        journal = {"status": "installing", "private_token": token,
                   "entries": entries, "environment_before": env_value(base)}
        audiofix.save(path, journal)
        try:
            for entry in entries:
                audiofix.copy_atomic(KIT / entry["name"], base / entry["path"])
            set_env(base, journal["environment_before"], ENABLED)
            journal["status"] = "installed"
            verify(base, journal)
            audiofix.save(path, journal)
        except BaseException:
            restore(base, state, journal)
            raise
    print("Detroit routing candidate installed with backups. No game was launched.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("ERROR:", error)
        raise SystemExit(1)
