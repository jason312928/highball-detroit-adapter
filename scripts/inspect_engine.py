#!/usr/bin/env python3
"""Record a local engine fingerprint without modifying a Highball installation."""
import argparse
from pathlib import Path
import adapter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--highball-root", type=Path, default=adapter.default_highball_root())
    parser.add_argument("--source-bottle", default="Games")
    parser.add_argument("--output", type=Path, default=adapter.KIT / "engine-lock.local.json")
    args = parser.parse_args()
    base = args.highball_root.expanduser().resolve()
    adapter.validate_base(base)
    if Path(args.source_bottle).name != args.source_bottle or args.source_bottle in [".", ".."]:
        parser.error("Invalid bottle name")
    settings = adapter.read(adapter.regular(base / "bottles" / args.source_bottle / "bottle.json"))
    engine_id = settings["engineID"]
    if engine_id != "x64-crossover26.3-r28":
        parser.error("Only the x64-crossover26.3-r28 engine baseline has been reviewed")
    engine = base / "engines" / engine_id
    if engine.is_symlink() or not engine.is_dir():
        parser.error("Engine directory must be a real directory")
    manifest = adapter.regular(engine / "manifest.json")
    if adapter.read(manifest).get("arch") != "x86_64":
        parser.error("Expected an x86_64 engine")
    wine = engine / "engine/bin/wine"
    library = engine / "frameworks/libMoltenVK.dylib"
    adapter.arch(wine)
    adapter.arch(library)
    record = dict(id=engine_id, manifest_sha256=adapter.sha(manifest),
                  wine_sha256=adapter.sha(wine), moltenvk_sha256=adapter.sha(library))
    output = args.output.expanduser().absolute()
    if output.is_symlink():
        parser.error("Output must not be a symlink")
    if output.exists() and adapter.read(adapter.regular(output)) != record:
        parser.error("Existing fingerprint differs; review the engine before replacing the local lock")
    adapter.save(output, record)
    print("Local engine fingerprint recorded. No game or Wine process was started.")


if __name__ == "__main__":
    main()
