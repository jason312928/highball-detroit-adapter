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
WSI_MARKER = b"HB_DETROIT_METALFX_WSI_V1"
HOST_BRIDGE_MARKER = b"hb_detroit_metalfx_surface_scaling_enabled"
BASELINE_WSI_SHA256 = "ae95ed75ffad3267c413d28fbcd46a360fe26c3de60fdd6ffeeff3510b891ab6"


def wsi_path(base):
    engine = adapter.targets(base)[0]
    path = adapter.regular(engine / "engine/lib/wine/x86_64-unix/win32u.so")
    if not path.resolve().is_relative_to(engine.resolve()):
        raise ValueError("WSI library escapes the private engine.")
    return path


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
    if r.get("wsi_original_sha256"):
        if r["wsi_original_sha256"] != BASELINE_WSI_SHA256:
            raise ValueError("Wine WSI baseline is not the reviewed r28 version.")
        wsi_backup = adapter.regular(directory / "original-win32u.so")
        if adapter.sha(wsi_backup) != r["wsi_original_sha256"]:
            raise ValueError("Original Wine WSI backup is damaged.")
    return r, backup


def verify_library(base, lib, j):
    directory = adapter.state_dir(base) / "metalfx-spatial-v1"
    if directory.is_symlink():
        raise ValueError("Unsafe MetalFX state directory.")
    r, _ = record_and_backup(directory, j)
    if adapter.sha(lib) != r.get("installed_sha256") or MARKER not in lib.read_bytes():
        raise ValueError("Private MetalFX library changed; refusing to accept it.")
    if not r.get("paired_wsi") or adapter.sha(wsi_path(base)) != r.get("wsi_installed_sha256"):
        raise ValueError("MetalFX requires its matching Wine WSI library; original Windows extent override is incompatible.")
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


def operate(base, action, library=None, apply=False, wsi_library=None):
    lib, directory, j = paths(base)
    current = adapter.sha(lib)
    record_path = directory / "transaction.json"
    old = None
    if os.path.lexists(record_path):
        old, _ = record_and_backup(directory, j)
    if action == "verify":
        if current == j["candidate_sha256"]:
            if old and old.get("paired_wsi") and adapter.sha(wsi_path(base)) != old["wsi_original_sha256"]:
                raise ValueError("Partial MetalFX WSI installation remains; run rollback.")
            adapter.log("Original private MoltenVK and WSI are installed; MetalFX is inactive.")
        else:
            r = verify_library(base, lib, j)
            adapter.log("Paired MetalFX spatial + Wine WSI verified, default scale 0.75; gameplay NOT established. SHA256=" + r["installed_sha256"])
        return
    bridge = wsi_path(base)
    bridge_current = adapter.sha(bridge)
    if action == "rollback":
        if not old:
            if current == j["candidate_sha256"]:
                adapter.log("Original engine already present.")
                return
            raise ValueError("No owned rollback record.")
        if current not in (j["candidate_sha256"], old["installed_sha256"]):
            raise ValueError("Unknown MoltenVK change; refusing rollback.")
        if old.get("paired_wsi") and bridge_current not in (old["wsi_original_sha256"], old["wsi_installed_sha256"]):
            raise ValueError("Unknown Wine WSI change; refusing rollback.")
        if current == j["candidate_sha256"] and (not old.get("paired_wsi") or bridge_current == old["wsi_original_sha256"]):
            adapter.log("Original private MoltenVK and WSI already present.")
            return
        updates = [(directory / "original.dylib", lib, current, j["candidate_sha256"])]
        if old.get("paired_wsi"):
            updates.append((directory / "original-win32u.so", bridge, bridge_current, old["wsi_original_sha256"]))
        r = old
    else:
        source = adapter.regular(library)
        if wsi_library is None:
            raise ValueError("A matching --wsi-library is required; MoltenVK-only installation is incompatible with Wine WSI.")
        source_bridge = adapter.regular(wsi_library)
        for candidate in (source, source_bridge):
            adapter.arch(candidate)
        if any(marker not in source.read_bytes() for marker in (MARKER, DEFAULT_MARKER, HOST_BRIDGE_MARKER, adapter.MARKER.encode())):
            raise ValueError("Candidate lacks paired MetalFX, default-on or strict-interface markers.")
        if WSI_MARKER not in source_bridge.read_bytes():
            raise ValueError("Wine WSI candidate marker is missing.")
        target_hash = adapter.sha(source)
        bridge_target = adapter.sha(source_bridge)
        if current != j["candidate_sha256"]:
            verify_library(base, lib, j)
            if current == target_hash and bridge_current == bridge_target:
                adapter.log("This paired MetalFX candidate is already installed.")
                return
            raise ValueError("Roll back the existing candidate before installing another.")
        bridge_original = old["wsi_original_sha256"] if old and old.get("paired_wsi") else bridge_current
        if bridge_original != BASELINE_WSI_SHA256:
            raise ValueError("Unsupported original Wine WSI version; no files changed.")
        if old and old.get("paired_wsi") and bridge_current not in (bridge_original, old["wsi_installed_sha256"]):
            raise ValueError("WSI changed outside the transaction.")
        r = {"policy": "detroit-metalfx-spatial-v1", "version": 2, "paired_wsi": True,
             "token": j["token"], "original_sha256": j["candidate_sha256"], "installed_sha256": target_hash,
             "wsi_original_sha256": bridge_original, "wsi_installed_sha256": bridge_target,
             "render_scale_default": 0.75, "enabled_by_default": True, "status": "prepared", "game_validated": False}
        # Publish the compatible bridge first. With the original host it stays inactive.
        updates = [(source_bridge, bridge, bridge_current, bridge_target), (source, lib, current, target_hash)]
    adapter.log(action + ": paired private Detroit MoltenVK / Wine WSI; no game launch.")
    if not apply:
        adapter.log("DRY-RUN: no file written. Use --apply to execute.")
        return
    game_stopped()
    with adapter.locked(base):
        if adapter.sha(lib) != current or adapter.sha(bridge) != bridge_current:
            raise ValueError("Engine files changed while acquiring lock.")
        directory.mkdir(mode=0o700, exist_ok=True)
        if action == "install":
            for original, name, expected in ((lib, "original.dylib", j["candidate_sha256"]),
                                              (bridge, "original-win32u.so", r["wsi_original_sha256"])):
                backup = directory / name
                if os.path.lexists(backup):
                    if adapter.sha(adapter.regular(backup)) != expected:
                        raise ValueError("Existing backup differs; refusing overwrite.")
                else:
                    if adapter.sha(original) != expected:
                        raise ValueError("Original file unavailable for backup.")
                    with backup.open("xb") as dst, original.open("rb") as src:
                        shutil.copyfileobj(src, dst)
                        dst.flush()
                        os.fsync(dst.fileno())
                    shutil.copystat(original, backup)
            adapter.save(record_path, r)
            record_and_backup(directory, j)
        changed = []
        try:
            for src, dst, expected, target in updates:
                if expected == target:
                    continue
                replace_file(src, dst, expected)
                changed.append((dst, target))
                if adapter.sha(dst) != target:
                    raise ValueError("Final checksum mismatch.")
        except BaseException:
            # If installation fails midway, restore the files already published.
            if action == "install":
                for dst, _ in reversed(changed):
                    backup = directory / ("original.dylib" if dst == lib else "original-win32u.so")
                    replace_file(backup, dst, adapter.sha(dst))
                r["status"] = "failed-restored"
                adapter.save(record_path, r)
            raise
        r["status"] = "installed" if action == "install" else "rolled-back"
        adapter.save(record_path, r)
        adapter.log("Verified: " + r["status"] + "; original files retained; game not launched.")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("install", "verify", "rollback"))
    p.add_argument("--library", type=Path)
    p.add_argument("--wsi-library", type=Path)
    p.add_argument("--highball-root", type=Path, default=adapter.default_highball_root())
    p.add_argument("--apply", action="store_true")
    a = p.parse_args()
    if a.action == "install" and (not a.library or not a.wsi_library):
        p.error("install requires --library and --wsi-library together")
    operate(a.highball_root.expanduser().resolve(), a.action, a.library, a.apply, a.wsi_library)


if __name__ == "__main__":
    main()
