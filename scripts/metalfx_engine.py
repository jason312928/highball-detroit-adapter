#!/usr/bin/env python3
"""Install/restore only the owned private Detroit MetalFX engine; dry-run by default."""
import argparse
import os
from pathlib import Path
import shutil
import tempfile

import adapter
from blur_workaround import game_stopped

MARKER = b"HB_DETROIT_METALFX_SPATIAL_V1"
DEFAULT_MARKER = b"HB_DETROIT_METALFX_DEFAULT_ON_V1"


def paths(base):
    adapter.validate_base(base)
    j = adapter.read(adapter.regular(adapter.state_dir(base) / "transaction.json"))
    engine, bottle = adapter.targets(base)
    if j.get("status") != "installed" or not all(adapter.owned(p, j["token"]) for p in (engine, bottle)):
        raise ValueError("An owned private Detroit installation is required.")
    lib = adapter.regular(engine / "frameworks/libMoltenVK.dylib")
    if not lib.resolve().is_relative_to(engine.resolve()):
        raise ValueError("Library escapes the private engine.")
    directory = adapter.state_dir(base) / "metalfx-spatial-v1"
    if directory.is_symlink():
        raise ValueError("Unsafe MetalFX backup directory.")
    return lib, directory, j


def record_and_backup(directory, j):
    r = adapter.read(adapter.regular(directory / "transaction.json"))
    if r.get("token") != j["token"] or r.get("original_sha256") != j["candidate_sha256"] or r.get("policy") != "detroit-metalfx-spatial-v1":
        raise ValueError("MetalFX record ownership or baseline mismatch.")
    backup = adapter.regular(directory / "original.dylib")
    if adapter.sha(backup) != j["candidate_sha256"]:
        raise ValueError("Original MoltenVK backup is damaged.")
    return r, backup


def verify_library(base, lib, j):
    directory = adapter.state_dir(base) / "metalfx-spatial-v1"
    if directory.is_symlink():
        raise ValueError("Unsafe MetalFX state directory.")
    r, _ = record_and_backup(directory, j)
    if adapter.sha(lib) != r.get("installed_sha256") or MARKER not in lib.read_bytes():
        raise ValueError("Private MetalFX library changed; refusing to accept it.")
    return r


def replace_file(src, dst, expected):
    fd, name = tempfile.mkstemp(prefix=".detroit-metalfx-", dir=dst.parent)
    os.close(fd)
    try:
        shutil.copy2(src, name)
        if adapter.sha(name) != adapter.sha(src) or adapter.sha(dst) != expected:
            raise ValueError("Library changed during replacement preparation.")
        with open(name, "rb") as f:
            os.fsync(f.fileno())
        game_stopped()
        os.replace(name, dst)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def operate(base, action, library=None, apply=False):
    lib, directory, j = paths(base)
    current = adapter.sha(lib)
    if action == "verify":
        if current == j["candidate_sha256"]:
            adapter.log("Original private MoltenVK is installed; MetalFX candidate is not active.")
        else:
            r = verify_library(base, lib, j)
            adapter.log("MetalFX spatial candidate verified: default enabled, render scale 0.75; game execution NOT established. SHA256=" + r["installed_sha256"])
        return
    if action == "rollback":
        if current == j["candidate_sha256"]:
            adapter.log("Original private MoltenVK already present.")
            return
        r = verify_library(base, lib, j)
        _, source = record_and_backup(directory, j)
        target_hash = j["candidate_sha256"]
    else:
        source = adapter.regular(library)
        adapter.arch(source)
        content = source.read_bytes()
        if any(marker not in content for marker in (MARKER, DEFAULT_MARKER, adapter.MARKER.encode())):
            raise ValueError("Candidate must contain MetalFX, default-on and strict-interface markers.")
        target_hash = adapter.sha(source)
        if current != j["candidate_sha256"]:
            verify_library(base, lib, j)
            if current == target_hash:
                adapter.log("This MetalFX candidate is already installed.")
                return
            raise ValueError("Roll back the existing candidate before installing another.")
    adapter.log(f"{action}: private Detroit MoltenVK only; target SHA256={target_hash}")
    if not apply:
        adapter.log("DRY-RUN: no file was written. Use --apply to execute.")
        return
    game_stopped()
    with adapter.locked(base):
        if adapter.sha(lib) != current:
            raise ValueError("Library changed while acquiring lock.")
        directory.mkdir(mode=0o700, exist_ok=True)
        if action == "install":
            backup = directory / "original.dylib"
            if os.path.lexists(backup):
                if adapter.sha(adapter.regular(backup)) != j["candidate_sha256"]:
                    raise ValueError("Existing original backup differs; refusing overwrite.")
            else:
                with backup.open("xb") as dst, lib.open("rb") as src:
                    shutil.copyfileobj(src, dst)
                    dst.flush()
                    os.fsync(dst.fileno())
                shutil.copystat(lib, backup)
            if os.path.lexists(directory / "transaction.json"):
                record_and_backup(directory, j)
            r = {"policy": "detroit-metalfx-spatial-v1", "token": j["token"], "original_sha256": j["candidate_sha256"],
                 "installed_sha256": target_hash, "render_scale_default": 0.75, "enabled_by_default": True, "status": "prepared", "game_validated": False}
            adapter.save(directory / "transaction.json", r)
            record_and_backup(directory, j)
        replace_file(source, lib, current)
        if adapter.sha(lib) != target_hash:
            raise ValueError("Final library checksum mismatch; original backup retained.")
        r["status"] = "installed" if action == "install" else "rolled-back"
        adapter.save(directory / "transaction.json", r)
        adapter.log("Verified: " + r["status"] + "; game was not launched.")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("install", "verify", "rollback"))
    p.add_argument("--library", type=Path)
    p.add_argument("--highball-root", type=Path, default=adapter.default_highball_root())
    p.add_argument("--apply", action="store_true")
    a = p.parse_args()
    if a.action == "install" and not a.library:
        p.error("install requires --library")
    operate(a.highball_root.expanduser().resolve(), a.action, a.library, a.apply)


if __name__ == "__main__":
    main()
