#!/usr/bin/env python3
"""Integration tests use tiny synthetic files, never the user's prefix or game."""
import argparse
import contextlib
import importlib.util
import io
import json
import os
import shutil
import sys
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location("adapter", Path(__file__).resolve().parents[1] / "scripts" / "adapter.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="Detroit adapter test space ")
        self.root = Path(self.temp.name).resolve()
        self.base = self.root / "Highball data"
        self.engine = self.base / "engines/x64-source"
        self.bottle = self.base / "bottles/Games"
        self.game = self.root / "Steam library/steamapps/common/Detroit Become Human"
        for p in [self.engine / "engine/bin", self.engine / "frameworks",
                  self.bottle / "drive_c/Program Files (x86)/Steam/steamapps",
                  self.bottle / "drive_c/users/test", self.game / "ShaderCache"]:
            p.mkdir(parents=True)
        self.candidate = self.root / "Candidate with space"
        self.candidate.mkdir()
        src = self.root / "fixture.c"
        src.write_text('const char *fixture_marker="HB_DETROIT_STRICT_INTERFACE_V1"; int main(void) { return 0; }\n')
        self.lib = self.candidate / "libMoltenVK.dylib"
        subprocess.run(["xcrun", "clang", "-arch", "x86_64", "-dynamiclib", str(src), "-o", str(self.lib)], check=True)
        subprocess.run(["xcrun", "clang", "-arch", "x86_64", str(src), "-o", str(self.engine / "engine/bin/wine")], check=True)
        (self.engine / "frameworks/libMoltenVK.dylib").write_bytes(self.lib.read_bytes())
        (self.bottle / "drive_c/Program Files (x86)/Steam/steam.exe").write_bytes(b"synthetic-not-a-game")
        (self.game / "DetroitBecomeHuman.exe").write_bytes(b"synthetic-exe")
        (self.game / "ShaderCache/CorruptedCache").touch()
        (self.game.parent.parent / "appmanifest_1222140.acf").write_text('"appid" "1222140"')
        (self.bottle / "drive_c/users/test/Documents").symlink_to(self.root)
        self.settings = {"engineID": "x64-source", "name": "Games"}
        m.save(self.bottle / "bottle.json", self.settings)
        component = {"kind": "runtime", "url": self.lib.as_uri(), "sha256": m.sha(self.lib)}
        m.save(self.engine / "manifest.json", {"id": "x64-source", "displayName": "Synthetic test fixture",
               "arch": "x86_64", "minMacOS": "14.0", "components": {"wine": component, "moltenvk": component}})
        self.cm = {"policy": "strict-interface-v1", "probe_passed": True, "dylib": self.lib.name, "sha256": m.sha(self.lib),
                   "moltenvk_commit": "8b511fdc5351a37c305bc246e161796ddca56b18",
                   "spirv_cross_commit": "05583ac1537d777d304128142de2365bfa4a38df",
                   "patch_sha256": m.sha(m.KIT / "patches/0001-strict-interfaces-and-pinned-spirv.patch")}
        self.manifest = self.candidate / "candidate.json"; m.save(self.manifest, self.cm)
        self.source_pin = mock.patch.object(m, "source_lock", return_value={
            "id": "x64-source", "manifest_sha256": m.sha(self.engine / "manifest.json"),
            "wine_sha256": m.sha(self.engine / "engine/bin/wine"),
            "moltenvk_sha256": m.sha(self.engine / "frameworks/libMoltenVK.dylib")})
        self.source_pin.start()
        self.a = argparse.Namespace(highball_root=self.base, source_bottle="Games", game_dir=self.game,
                                   candidate_manifest=self.manifest, apply=True, dry_run=False)
        self.quiet = mock.patch.object(m, "quiet_required"); self.quiet.start()
        self.output = contextlib.redirect_stdout(io.StringIO()); self.output.__enter__()
        self.original = self.hashes()

    def tearDown(self):
        self.assertEqual(self.original, self.hashes(), "source files were modified")
        self.output.__exit__(None, None, None); self.quiet.stop(); self.source_pin.stop(); self.temp.cleanup()

    def hashes(self):
        return {str(p): m.sha(p) for root in [self.engine, self.bottle, self.game]
                for p in root.rglob("*") if p.is_file() and not p.is_symlink()}

    def test_dry_run_no_writes(self):
        self.a.apply = False
        self.assertEqual(m.install(self.a), 0)
        self.assertFalse((self.base / ".detroit-adapter").exists())
        self.assertTrue(all(not p.exists() for p in m.targets(self.base)))

    def test_engine_inspection_writes_only_local_hashes(self):
        inspected = self.root / "inspection space"
        engine_id = "x64-crossover26.3-r28"
        engine = inspected / "engines" / engine_id
        engine.parent.mkdir(parents=True)
        shutil.copytree(self.engine, engine)
        bottle = inspected / "bottles/Games"
        bottle.mkdir(parents=True)
        m.save(bottle / "bottle.json", {"engineID": engine_id})
        output = self.root / "engine-lock.local.json"
        command = [sys.executable, str(m.KIT / "scripts/inspect_engine.py"),
                   "--highball-root", str(inspected), "--output", str(output)]
        result = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        record = m.read(output)
        self.assertEqual(set(record), {"id", "manifest_sha256", "wine_sha256", "moltenvk_sha256"})
        self.assertNotIn(str(self.root), output.read_text())

    def test_install_repeat_verify_rollback_repeat(self):
        self.assertEqual(m.install(self.a), 0)
        e, b = m.targets(self.base)
        self.assertEqual(m.install(self.a), 0)
        m.verify_installed(self.base)
        self.assertFalse((b / "drive_c/users/test/Documents").is_symlink())
        self.assertEqual(m.rollback(self.a), 0)
        self.assertEqual(m.rollback(self.a), 0)
        self.assertFalse(e.exists()); self.assertFalse(b.exists())
        j = m.read(self.base / ".detroit-adapter/transaction.json")
        self.assertTrue((Path(j["archive"]) / "bottle/drive_c/DetroitSteamLibrary/steamapps/common/Detroit Become Human/ShaderCache.before-detroit-adapter/CorruptedCache").exists())

    def test_failure_after_first_publish_restores(self):
        replace = m.os.replace
        def fail(src, dst):
            if Path(dst) == m.targets(self.base)[1]:
                raise OSError("injected second publish failure")
            return replace(src, dst)
        with mock.patch.object(m.os, "replace", side_effect=fail):
            with self.assertRaises(OSError): m.install(self.a)
        self.assertTrue(all(not p.exists() for p in m.targets(self.base)))
        self.assertEqual(m.read(self.base / ".detroit-adapter/transaction.json")["status"], "failed-restored")
        self.assertEqual(m.install(self.a), 0)

    def test_failure_during_copy_restores(self):
        copy = m.copy_tree
        def fail(src, dst):
            if Path(src) == self.game: raise OSError("injected disk failure")
            copy(src, dst)
        with mock.patch.object(m, "copy_tree", side_effect=fail):
            with self.assertRaises(OSError): m.install(self.a)
        self.assertTrue(all(not p.exists() for p in m.targets(self.base)))

    def test_checksum_tamper_refused(self):
        self.lib.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "SHA-256"): m.install(self.a)
        self.assertFalse((self.base / ".detroit-adapter").exists())

    def test_unowned_target_never_overwritten(self):
        m.targets(self.base)[0].mkdir()
        with self.assertRaisesRegex(ValueError, "overwrite"): m.install(self.a)

    def test_symlinked_state_refused(self):
        (self.base / ".detroit-adapter").symlink_to(self.root)
        with self.assertRaisesRegex(ValueError, "symlink"): m.install(self.a)

    def test_private_lib_tamper_detected(self):
        m.install(self.a)
        (m.targets(self.base)[0] / "frameworks/libMoltenVK.dylib").write_bytes(b"bad")
        with self.assertRaises(Exception): m.verify_installed(self.base)

    def test_raw_release_policy_refused(self):
        self.cm["policy"] = "release003"
        m.save(self.manifest, self.cm)
        with self.assertRaisesRegex(ValueError, "strict"): m.install(self.a)

    def test_copy_path_escape_refused(self):
        with self.assertRaisesRegex(ValueError, "escapes"):
            m.private_path(self.bottle, "drive_c/users/test/Documents/anything")

    def test_arm64_candidate_refused(self):
        subprocess.run(["xcrun", "clang", "-arch", "arm64", "-dynamiclib", str(self.root / "fixture.c"),
                        "-o", str(self.lib)], check=True)
        self.cm["sha256"] = m.sha(self.lib); m.save(self.manifest, self.cm)
        with self.assertRaisesRegex(ValueError, "x86_64"): m.install(self.a)

    def test_interrupted_install_is_recovered(self):
        state = self.base / ".detroit-adapter"; state.mkdir()
        e, _ = m.targets(self.base); e.mkdir()
        token = "test-interrupted"
        m.save(e / m.OWNER, {"token": token})
        stage = state / ("stage-" + token); stage.mkdir()
        m.save(stage / m.OWNER, {"token": token})
        m.save(state / "transaction.json", {"token": token, "status": "installing"})
        self.assertEqual(m.install(self.a), 0)
        self.assertFalse(stage.exists())

    def test_rollback_dry_run_no_moves(self):
        m.install(self.a); self.a.apply = False
        self.assertEqual(m.rollback(self.a), 0)
        self.assertTrue(all(p.exists() for p in m.targets(self.base)))

    def test_rollback_failure_restores_published_paths(self):
        m.install(self.a)
        replace = m.os.replace
        def fail(src, dst):
            if Path(src) == m.targets(self.base)[1]: raise OSError("injected rollback failure")
            return replace(src, dst)
        with mock.patch.object(m.os, "replace", side_effect=fail):
            with self.assertRaises(OSError): m.rollback(self.a)
        m.verify_installed(self.base)

    def test_log_load_does_not_establish_game_progress(self):
        path = self.root / "game.log"
        path.write_text("dyld[123]: " + str(m.targets(self.base)[0] / "frameworks/libMoltenVK.dylib") + "\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            result = m.verify_log(self.base, path)
        self.assertEqual(result, 0)
        report = json.loads(out.getvalue())
        self.assertEqual(report["main_menu"], "UNVERIFIED")
        self.assertEqual(report["shader_98_percent_completed"], "UNVERIFIED")
        self.assertFalse(report["daily_use_safe"])

    def test_log_failure_remains_failure(self):
        path = self.root / "game.log"
        path.write_text("dyld[123]: " + str(m.targets(self.base)[0] / "frameworks/libMoltenVK.dylib") +
                        "\nRender pipeline compile failed\n")
        self.assertEqual(m.verify_log(self.base, path), 4)

    def test_log_environment_header_is_not_load_proof(self):
        path = self.root / "game.log"
        path.write_text("# DYLD_FALLBACK_LIBRARY_PATH=" + str(m.targets(self.base)[0] / "frameworks") + "\n")
        self.assertEqual(m.verify_log(self.base, path), 4)

    @unittest.skipUnless(os.environ.get("HIGHBALL_TEST_CLI"), "optional compiled Highball CLI integration")
    def test_highball_cli_decodes_private_profile(self):
        m.install(self.a)
        cli = os.environ["HIGHBALL_TEST_CLI"]
        env = dict(os.environ, HIGHBALL_HOME=str(self.base))
        result = subprocess.run([cli, "env", "Detroit Isolated"], env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('MVK_CONFIG_SHADER_COMPRESSION_ALGORITHM="3"', result.stdout)
        self.assertIn('MVK_CONFIG_SHOULD_MAXIMIZE_CONCURRENT_COMPILATION="1"', result.stdout)
        self.assertIn(str(m.targets(self.base)[0] / "frameworks"), result.stdout)
        self.assertNotIn(str(self.engine / "frameworks"), result.stdout)

if __name__ == "__main__":
    unittest.main(verbosity=2)
