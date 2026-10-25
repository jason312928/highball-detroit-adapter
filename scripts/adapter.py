#!/usr/bin/env python3
"""Detroit-only Highball adapter. Dry-run by default. No shell interpolation or sudo."""
import argparse
import contextlib
import datetime
import fcntl
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import signal
import struct
import subprocess
import sys
import uuid

KIT = Path(__file__).resolve().parent.parent
MARKER = "HB_DETROIT_STRICT_INTERFACE_V1"
OWNER = ".detroit-adapter-owner.json"
ENGINE_NAME = "detroit-strict-003-r28"
BOTTLE_NAME = "Detroit Isolated"
APPID = "1222140"
RUNTIME_DLLS = ("msvcp140.dll", "mfc140.dll", "vcruntime140.dll")

def check_runtime(game, bottle):
    """Check the game's required VC runtime before cloning; never distribute it."""
    for name in RUNTIME_DLLS:
        paths = [game / name, bottle / "drive_c/windows/system32" / name]
        dll = next((p for p in paths if p.is_file()), None)
        if dll is None:
            raise ValueError(f"Missing x64 Visual C++ runtime: {name}. Install the Microsoft x64 VC runtime in the source environment, then retry.")
        regular(dll)
        with dll.open("rb") as f:
            header = f.read(64)
            if len(header) < 64 or header[:2] != b"MZ":
                raise ValueError(f"Invalid PE runtime: {name}")
            offset = struct.unpack_from("<I", header, 60)[0]
            if offset > 1024 * 1024:
                raise ValueError(f"Invalid PE runtime offset: {name}")
            f.seek(offset)
            if f.read(6) != b"PE\0\0\x64\x86":
                raise ValueError(f"Expected x86_64 Visual C++ runtime: {name}")

def default_highball_root():
    default = Path.home() / "Library/Application Support/Highball"
    if os.environ.get("HIGHBALL_HOME"):
        return Path(os.environ["HIGHBALL_HOME"])
    config = default / "config.json"
    if config.is_file():
        configured = Path(read(config).get("home", str(default))).expanduser()
        if configured.is_dir():
            return configured
    return default

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()

def run(args, **kw):
    r = subprocess.run([str(a) for a in args], text=True, capture_output=True, **kw)
    if r.returncode:
        raise RuntimeError(f"Command failed ({r.returncode}): {args}\n{r.stdout}\n{r.stderr}")
    return r.stdout.strip()

def log(s):
    print(s, flush=True)

def save(path, value):
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

def read(path):
    return json.loads(Path(path).read_text())

def regular(path):
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"Expected a regular file: {path}")
    return path

def source_lock():
    path = KIT / "engine-lock.local.json"
    if not path.is_file():
        raise ValueError("Missing local engine fingerprint. Run scripts/inspect_engine.py before installation planning.")
    return read(regular(path))

def arch(path):
    path = regular(path)
    values = run(["/usr/bin/lipo", "-archs", path]).split()
    if "x86_64" not in values:
        raise ValueError(f"x86_64 slice missing: {path}: {values}")
    return values

def candidate(path):
    m = read(regular(path))
    if m.get("policy") != "strict-interface-v1":
        raise ValueError("Candidate must be built by build.sh with the strict interface patch.")
    if not m.get("probe_passed"):
        raise ValueError("Candidate must pass the Rosetta/config/Vulkan probe before installation.")
    dylib = (Path(path).resolve().parent / m["dylib"]).resolve()
    regular(dylib)
    if sha(dylib) != m["sha256"]:
        raise ValueError("Candidate SHA-256 mismatch.")
    arch(dylib)
    if MARKER.encode() not in dylib.read_bytes():
        raise ValueError("Strict interface diagnostic marker missing.")
    if m.get("moltenvk_commit") != "8b511fdc5351a37c305bc246e161796ddca56b18":
        raise ValueError("Unexpected MoltenVK base commit.")
    if m.get("spirv_cross_commit") != "05583ac1537d777d304128142de2365bfa4a38df":
        raise ValueError("Unexpected SPIRV-Cross pin.")
    if m.get("patch_sha256") != sha(KIT / "patches/0001-strict-interfaces-and-pinned-spirv.patch"):
        raise ValueError("Candidate was built with a different patch.")
    return dylib, m

def quiet_required():
    # Never kill a user's process. A consistent clone requires a stopped source prefix.
    rows = run(["/bin/ps", "-axo", "comm="]).splitlines()
    live = [s for s in rows if (
        s.endswith("/Highball") or s.endswith("/wine") or s.endswith("/wineserver")
        or s.lower().endswith(".exe"))]
    if live:
        raise ValueError("Close Highball and Wine/Windows programs before --apply; nothing was stopped.")

def validate_base(base):
    if not base.is_dir() or base.is_symlink():
        raise ValueError("Highball data root must be an existing real directory.")
    for child in ["engines", "bottles"]:
        p = base / child
        if not p.is_dir() or p.is_symlink():
            raise ValueError(f"Unsafe Highball subdirectory: {p}")

def targets(base):
    return [base / "engines" / ENGINE_NAME, base / "bottles" / BOTTLE_NAME]

def owned(path, token):
    return not path.is_symlink() and (path / OWNER).is_file() and read(path / OWNER).get("token") == token

def state_dir(base):
    p = base / ".detroit-adapter"
    if p.is_symlink():
        raise ValueError("State directory must not be a symlink.")
    if (p / "transaction.json").is_symlink():
        raise ValueError("Transaction file must not be a symlink.")
    return p

def recover(base, journal):
    # Only new paths from this transaction can be removed; shared paths are never targets.
    token = journal["token"]
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", token):
        raise ValueError("Unsafe transaction token.")
    for p in targets(base):
        if os.path.lexists(p):
            if not owned(p, token):
                raise ValueError(f"Recovery refused an unowned path: {p}")
            shutil.rmtree(p)
    stage = state_dir(base) / ("stage-" + token)
    if stage.exists():
        if not owned(stage, token):
            raise ValueError("Recovery stage ownership mismatch.")
        shutil.rmtree(stage)
    journal["status"] = "failed-restored"
    save(state_dir(base) / "transaction.json", journal)
    log("Failure recovery complete: only newly created private paths removed.")

@contextlib.contextmanager
def locked(base):
    directory = state_dir(base)
    directory.mkdir(mode=0o700, exist_ok=True)
    lock = directory / "lock"
    if lock.is_symlink():
        raise ValueError("Lock must not be a symlink.")
    with lock.open("a") as f:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield directory

def copy_tree(src, dst):
    # APFS clonefile when possible; copy fallback for exFAT -> APFS. Never hardlink.
    log(f"COPY {src} -> {dst}")
    result = subprocess.run(["/bin/cp", "-cR", str(src), str(dst)], capture_output=True, text=True)
    if result.returncode:
        log("clonefile unavailable; falling back to independent file copies.")
        if dst.exists():
            shutil.rmtree(dst)
        run(["/usr/bin/ditto", src, dst])

def private_path(root, relative):
    """Ensure a copied path cannot write through an absolute or escaping symlink."""
    p = root / relative
    if not p.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Copied path escapes private stage: {p}")
    return p

def relocate_links(root, replacements):
    for folder, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            p = Path(folder) / name
            if not p.is_symlink():
                continue
            target = os.readlink(p)
            if not os.path.isabs(target):
                continue
            for old, new in replacements:
                if target == str(old) or target.startswith(str(old) + "/"):
                    p.unlink()
                    p.symlink_to(str(new) + target[len(str(old)):])
                    break

def plan(a):
    base = a.highball_root.expanduser().resolve()
    validate_base(base)
    source_bottle = base / "bottles" / a.source_bottle
    if source_bottle.is_symlink() or not source_bottle.is_dir():
        raise ValueError("Source bottle must be a real directory.")
    settings = read(regular(source_bottle / "bottle.json"))
    engine_id = settings["engineID"]
    if Path(engine_id).name != engine_id:
        raise ValueError("Unsafe engine ID.")
    source_engine = base / "engines" / engine_id
    if source_engine.is_symlink() or not source_engine.is_dir():
        raise ValueError("Source engine must be a real directory.")
    manifest = read(regular(source_engine / "manifest.json"))
    if manifest.get("arch") != "x86_64":
        raise ValueError("This adapter targets the inspected Rosetta/x86_64 engine only.")
    wine = source_engine / "engine/bin/wine"
    source_lib = source_engine / "frameworks/libMoltenVK.dylib"
    arch(wine); arch(source_lib)
    pinned = source_lock()
    if (engine_id != pinned["id"] or sha(source_engine / "manifest.json") != pinned["manifest_sha256"]
        or sha(wine) != pinned["wine_sha256"] or sha(source_lib) != pinned["moltenvk_sha256"]):
        raise ValueError("Source engine differs from the inspected/pinned environment; re-audit before installation.")
    if a.game_dir is None:
        raise ValueError("Specify --game-dir; no machine-specific path is stored in this source distribution.")
    game = a.game_dir.expanduser().resolve()
    regular(game / "DetroitBecomeHuman.exe")
    check_runtime(game, source_bottle)
    # Require a Steam installation so the private Steam library can be registered correctly.
    appmanifest = game.parent.parent / f"appmanifest_{APPID}.acf"
    regular(appmanifest)
    engine, bottle = targets(base)
    log(f"Source bottle: {source_bottle}\nSource engine: {source_engine}")
    log(f"Wine SHA-256: {sha(wine)}\nCurrent MoltenVK SHA-256: {sha(source_lib)}")
    log(f"Game EXE SHA-256: {sha(game / 'DetroitBecomeHuman.exe')}")
    log(f"Private engine: {engine}\nPrivate bottle: {bottle}")
    log("Plan: independent copies of engine, bottle and Detroit game; fresh cache only in the private game copy.")
    log("No source cache, game EXE, graphics options, shared engine or system Vulkan file is changed.")
    if not a.candidate_manifest:
        log("BLOCKED: no strict candidate binary exists yet. Release003 is probe-only.")
        return base, None
    dylib, cm = candidate(a.candidate_manifest)
    log(f"Strict candidate: {dylib}\nSHA-256: {cm['sha256']}")
    return base, (source_engine, source_bottle, settings, manifest, game, appmanifest, dylib, cm)

def install(a):
    base, data = plan(a)
    if not data:
        if a.apply:
            raise ValueError("Cannot install without a strict build.")
        return 3
    if not a.apply:
        log("DRY-RUN complete. No Highball or game files written.")
        return 0
    source_engine, source_bottle, settings, manifest, game, appmanifest, dylib, cm = data
    with locked(base) as state:
        journal_path = state / "transaction.json"
        old = read(journal_path) if journal_path.exists() else None
        if old and old["status"] == "installing":
            recover(base, old)
        elif old and old["status"] == "installed":
            if all(owned(p, old["token"]) for p in targets(base)) and old["candidate_sha256"] == cm["sha256"]:
                verify_installed(base)
                log("Already installed; no files changed.")
                return 0
            raise ValueError("Existing private install differs; rollback before replacing.")
        for p in targets(base):
            if os.path.lexists(p):
                raise ValueError(f"Refusing to overwrite existing path: {p}")
        quiet_required()
        total = 0
        for root in [source_engine, source_bottle, game]:
            for folder, _, files in os.walk(root, followlinks=False):
                for name in files:
                    p = Path(folder) / name
                    if not p.is_symlink():
                        total += p.stat().st_size
        free = shutil.disk_usage(base).free
        log(f"Conservative copy space: {total} bytes; free: {free} bytes.")
        if free < total + 12 * 1024**3:
            raise ValueError("Insufficient space for independent copies plus 12 GiB tool/cache reserve.")
        token = uuid.uuid4().hex
        stage = state / ("stage-" + token)
        stage.mkdir()
        save(stage / OWNER, {"token": token})
        j = {"token": token, "status": "installing", "candidate_sha256": cm["sha256"],
             "source_exe_sha256": sha(game / "DetroitBecomeHuman.exe")}
        save(journal_path, j)
        try:
            se, sb = stage / "engine", stage / "bottle"
            copy_tree(source_engine, se); save(se / OWNER, {"token": token})
            copy_tree(source_bottle, sb); save(sb / OWNER, {"token": token})
            private_game = private_path(sb, "drive_c/DetroitSteamLibrary/steamapps/common/Detroit Become Human")
            if private_game.exists():
                raise ValueError("Source bottle already has a private Detroit library.")
            private_game.parent.mkdir(parents=True)
            copy_tree(game, private_game)
            if sha(private_game / "DetroitBecomeHuman.exe") != j["source_exe_sha256"]:
                raise ValueError("Private game executable copy failed checksum.")
            # Preserve old caches as backups only in the new, unpublished copy.
            cache = private_game / "ShaderCache"
            if cache.exists():
                cache.rename(private_game / "ShaderCache.before-detroit-adapter")
            shutil.copy2(appmanifest, sb / f"drive_c/DetroitSteamLibrary/steamapps/appmanifest_{APPID}.acf")
            steam = private_path(sb, "drive_c/Program Files (x86)/Steam")
            regular(steam / "steam.exe")
            private_path(sb, "drive_c/Program Files (x86)/Steam/steamapps/libraryfolders.vdf")
            vdf = '"libraryfolders"\n{\n "0"\n {\n  "path" "C:\\\\Program Files (x86)\\\\Steam"\n  "apps" { }\n }\n "1"\n {\n  "path" "C:\\\\DetroitSteamLibrary"\n  "apps" { "1222140" "0" }\n }\n}\n'
            (steam / "steamapps/libraryfolders.vdf").write_text(vdf)
            # Detach standard Wine user folder links to avoid shared Documents/saves.
            users = private_path(sb, "drive_c/users")
            for user in users.iterdir():
                if user.is_dir() and not user.is_symlink():
                    for name in ["Desktop", "Documents", "Downloads", "Music", "Pictures", "Videos", "Saved Games"]:
                        p = user / name
                        if p.is_symlink():
                            p.unlink(); p.mkdir()
            engine, bottle = targets(base)
            relocate_links(se, [(source_engine, engine)])
            relocate_links(sb, [(source_engine, engine), (source_bottle, bottle)])
            lib = se / "frameworks/libMoltenVK.dylib"
            private_path(se, "frameworks/libMoltenVK.dylib")
            regular(lib)
            shutil.copyfile(dylib, lib)
            if sha(lib) != cm["sha256"]:
                raise ValueError("Installed candidate checksum failed.")
            # Absolute private library search paths are used; no global DYLD override.
            env = {
                "MVK_CONFIG_SHADER_COMPRESSION_ALGORITHM": "3",
                "MVK_CONFIG_SHOULD_MAXIMIZE_CONCURRENT_COMPILATION": "1",
                "VK_DTR_MSL_LIBRARY_DISK_CACHE_DIR": str(bottle / ".detroit-cache/msl"),
                "MVK_CONFIG_SHADER_DUMP_DIR": str(bottle / ".detroit-cache/shader-dumps"),
                "DYLD_PRINT_LIBRARIES": "1",
            }
            for d in ["msl", "shader-dumps"]:
                (sb / ".detroit-cache" / d).mkdir(parents=True, exist_ok=True)
            manifest["id"] = ENGINE_NAME
            manifest["displayName"] = "Detroit strict diagnostic (unverified)"
            manifest.setdefault("baseEnv", {}).update(env)
            # Preserve the original Wine build identity to avoid switching to a different Wine.
            archive = se / "detroit-component.tar.gz"
            run(["/usr/bin/tar", "-czf", archive, "-C", se / "frameworks", "libMoltenVK.dylib"])
            manifest["components"]["moltenvk"] = {
                "kind": "runtime", "url": (engine / archive.name).as_uri(),
                "sha256": sha(archive), "size": archive.stat().st_size,
                "license": "Apache-2.0", "order": 2,
                "extract": {"into": "frameworks/libMoltenVK.dylib", "subpath": "libMoltenVK.dylib"},
                "version": "Detroit strict diagnostic; gameplay unverified"}
            save(se / "manifest.json", manifest)
            settings.update(name=BOTTLE_NAME, engineID=ENGINE_NAME, environment=env,
                            gameEnvironment={}, renderer="dxmt", frameGen=1,
                            externalDrives=[],
                            engineAppDefaultsSynced=ENGINE_NAME + ":")
            # Do not carry the source Bottle's other Steam-library drive mappings.
            drives = private_path(sb, "dosdevices")
            if drives.is_dir():
                for drive in drives.iterdir():
                    if drive.is_symlink() and drive.name.lower() not in ["c:", "z:"]:
                        drive.unlink()
            settings["pins"] = [{"id": str(uuid.uuid4()).upper(), "name": "Detroit (isolated Steam)",
                "path": "Program Files (x86)/Steam/steam.exe", "arguments": ["-applaunch", APPID],
                "environment": {"WINEMSYNC": "0", "WINEESYNC": "0"}}]
            save(sb / "bottle.json", settings)
            save(se / "detroit-provenance.json", cm)
            os.replace(se, engine)
            os.replace(sb, bottle)
            j["status"] = "installed"
            save(journal_path, j)
            shutil.rmtree(stage)
            log("Private diagnostic engine and Bottle installed. No game was launched.")
        except BaseException:
            recover(base, j)
            raise
    return 0

def verify_installed(base):
    validate_base(base)
    state = state_dir(base) / "transaction.json"
    j = read(regular(state))
    if j["status"] != "installed":
        raise ValueError(f"Not installed: {j['status']}")
    e, b = targets(base)
    if not all(owned(p, j["token"]) for p in [e, b]):
        raise ValueError("Private installation ownership mismatch.")
    lib = regular(e / "frameworks/libMoltenVK.dylib")
    arch(lib)
    if sha(lib) != j["candidate_sha256"]:
        from metalfx_engine import verify_library
        verify_library(base, lib, j)
        log("Private MetalFX spatial override verified; gameplay remains unverified.")
    exe = b / "drive_c/DetroitSteamLibrary/steamapps/common/Detroit Become Human/DetroitBecomeHuman.exe"
    if sha(exe) != j["source_exe_sha256"]:
        from blur_workaround import verify_executable
        log("EXE state: " + verify_executable(base, exe, j))
    settings = read(b / "bottle.json")
    if settings["engineID"] != ENGINE_NAME:
        raise ValueError("Private Bottle changed engines.")
    log(f"Installed files verified: {lib}\nGame progress is NOT established by this check.")

def rollback(a):
    base = a.highball_root.expanduser().resolve()
    validate_base(base)
    state = state_dir(base)
    path = state / "transaction.json"
    if not path.exists():
        log("Nothing installed; rollback is already complete.")
        return 0
    j = read(regular(path))
    if j["status"] in ["rolled-back", "failed-restored"]:
        log("Already rolled back.")
        return 0
    log("Rollback archives only the private engine/Bottle, including saves; source installation remains untouched.")
    if not a.apply:
        log("DRY-RUN: no files moved.")
        return 0
    quiet_required()
    with locked(base):
        j = read(path)
        if j["status"] == "installing":
            recover(base, j)
            return 0
        token = j["token"]
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", token):
            raise ValueError("Unsafe transaction token.")
        archive = state / "archived" / token
        archive.mkdir(parents=True, exist_ok=True)
        moved = []
        try:
            for p, name in zip(targets(base), ["engine", "bottle"]):
                dest = archive / name
                if not os.path.lexists(p):
                    if owned(dest, token):
                        continue  # recover a rollback interrupted after one rename
                    raise ValueError(f"Private path disappeared: {p}")
                if not owned(p, token) or dest.exists():
                    raise ValueError("Refusing rollback of an unowned or conflicting path.")
                os.replace(p, dest); moved.append((dest, p))
            j["status"] = "rolled-back"; j["archive"] = str(archive)
            save(path, j)
        except BaseException:
            for src, dest in reversed(moved):
                os.replace(src, dest)
            raise
        log(f"Rollback complete. Private data preserved at {archive}")
    return 0

def verify_log(base, path):
    text = regular(path).read_text(errors="replace")
    expected = str(targets(base)[0] / "frameworks/libMoltenVK.dylib")
    images = [line for line in text.splitlines()
              if line.startswith("dyld[") and "libMoltenVK.dylib" in line]
    failures = [line for line in text.splitlines() if any(s in line.lower() for s in [
        "render pipeline compile failed", "missing from the vertex descriptor",
        "hb_detroit_strict_interface_v1:", "unhandled exception", "footprint limit"])]
    report = {"expected_image": expected, "dyld_image_lines": images,
              "private_library_load_observed": any(expected in line for line in images),
              "failure_line_count": len(failures), "failure_examples": failures[:10],
              "shader_98_percent_completed": "UNVERIFIED",
              "main_menu": "UNVERIFIED", "scene_started_and_rendered": "UNVERIFIED",
              "daily_use_safe": False}
    log(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["private_library_load_observed"] and not failures else 4

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("operation", choices=["install", "verify", "rollback"])
    p.add_argument("--highball-root", type=Path, default=default_highball_root())
    p.add_argument("--source-bottle", default="Games")
    p.add_argument("--game-dir", type=Path, help="Detroit game directory; required for install planning.")
    p.add_argument("--candidate-manifest", type=Path)
    p.add_argument("--game-log", type=Path, help="Read an actual Highball/Wine log; never infers menu or scene success.")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true", help="Only after explicit user authorization. Closes nothing automatically.")
    a = p.parse_args(argv)
    if Path(a.source_bottle).name != a.source_bottle or a.source_bottle in [".", ".."]:
        p.error("source-bottle must be a directory name")
    if a.operation == "install": return install(a)
    if a.operation == "rollback": return rollback(a)
    if a.dry_run and not a.candidate_manifest and not (state_dir(a.highball_root.expanduser().resolve()) / "transaction.json").exists():
        _, data = plan(a)
        return 0 if data else 3
    if a.candidate_manifest:
        lib, m = candidate(a.candidate_manifest)
        log(f"Candidate verified: {lib}\nSHA-256={m['sha256']}; gameplay remains unverified.")
    else:
        verify_installed(a.highball_root.expanduser().resolve())
    if a.game_log:
        return verify_log(a.highball_root.expanduser().resolve(), a.game_log)
    return 0

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        sys.exit(main())
    except (Exception, KeyboardInterrupt) as e:
        log(f"ERROR: {type(e).__name__}: {e}")
        sys.exit(1)
