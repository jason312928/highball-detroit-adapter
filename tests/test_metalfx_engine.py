"""Private engine transactions use synthetic files, never a real game."""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import metalfx_engine as m


class MetalFXEngineTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.base = Path(t.name)
        for target in m.adapter.targets(self.base):
            target.mkdir(parents=True)
            m.adapter.save(target / m.adapter.OWNER, {"token": "test"})
        self.lib = m.adapter.targets(self.base)[0] / "frameworks/libMoltenVK.dylib"
        self.lib.parent.mkdir()
        self.lib.write_bytes(b"original-engine")
        self.candidate = self.base / "candidate.dylib"
        self.candidate.write_bytes(m.MARKER + m.DEFAULT_MARKER + m.HOST_BRIDGE_MARKER + m.adapter.MARKER.encode())
        self.wsi = m.adapter.targets(self.base)[0] / "engine/lib/wine/x86_64-unix/win32u.so"
        self.wsi.parent.mkdir(parents=True)
        self.wsi.write_bytes(b"original-wsi")
        pin = mock.patch.object(m, "BASELINE_WSI_SHA256", m.adapter.sha(self.wsi))
        pin.start()
        self.addCleanup(pin.stop)
        self.bridge = self.base / "wsi-candidate.so"
        self.bridge.write_bytes(m.WSI_MARKER)
        self.state = m.adapter.state_dir(self.base)
        self.state.mkdir()
        self.j = {"token": "test", "status": "installed", "candidate_sha256": m.adapter.sha(self.lib)}
        m.adapter.save(self.state / "transaction.json", self.j)
        self.directory = self.state / "metalfx-spatial-v1"
        for name in ("game_stopped",):
            p = mock.patch.object(m, name)
            self.guard = p.start()
            self.addCleanup(p.stop)
        p = mock.patch.object(m.adapter, "arch")
        p.start()
        self.addCleanup(p.stop)
        out = contextlib.redirect_stdout(io.StringIO())
        out.__enter__()
        self.addCleanup(out.__exit__, None, None, None)

    def test_dry_run_writes_nothing(self):
        m.operate(self.base, "install", self.candidate, wsi_library=self.bridge)
        self.assertFalse(self.directory.exists())
        self.assertEqual(self.lib.read_bytes(), b"original-engine")
        self.assertEqual(self.wsi.read_bytes(), b"original-wsi")

    def test_install_verify_repeat_and_full_restore(self):
        m.operate(self.base, "install", self.candidate, True, wsi_library=self.bridge)
        m.operate(self.base, "verify")
        m.operate(self.base, "install", self.candidate, True, wsi_library=self.bridge)
        self.assertEqual(self.lib.read_bytes(), self.candidate.read_bytes())
        m.operate(self.base, "rollback", apply=True)
        m.operate(self.base, "rollback", apply=True)
        self.assertEqual(self.lib.read_bytes(), b"original-engine")
        self.assertEqual(self.wsi.read_bytes(), b"original-wsi")
        self.assertEqual(m.adapter.read(self.state / "transaction.json"), self.j)

    def test_missing_default_on_refused(self):
        self.candidate.write_bytes(m.MARKER + m.adapter.MARKER.encode())
        with self.assertRaises(ValueError):
            m.operate(self.base, "install", self.candidate, True, wsi_library=self.bridge)
        self.assertFalse(self.directory.exists())

    def test_running_game_refused(self):
        self.guard.side_effect = ValueError("game running")
        with self.assertRaises(ValueError):
            m.operate(self.base, "install", self.candidate, True, wsi_library=self.bridge)
        self.assertFalse(self.directory.exists())

    def test_unknown_drift_refused(self):
        m.operate(self.base, "install", self.candidate, True, wsi_library=self.bridge)
        self.lib.write_bytes(b"changed")
        with self.assertRaises(ValueError):
            m.operate(self.base, "rollback", apply=True)
        self.assertEqual(self.lib.read_bytes(), b"changed")

    def test_corrupt_backup_refused(self):
        m.operate(self.base, "install", self.candidate, True, wsi_library=self.bridge)
        (self.directory / "original.dylib").write_bytes(b"bad")
        with self.assertRaises(ValueError):
            m.operate(self.base, "verify")

    def test_symlink_backup_refused(self):
        self.directory.symlink_to(self.lib.parent, target_is_directory=True)
        with self.assertRaises(ValueError):
            m.operate(self.base, "install", self.candidate, True, wsi_library=self.bridge)

    def test_interrupted_publish_can_retry(self):
        with mock.patch.object(m, "replace_file", side_effect=OSError("injected failure")):
            with self.assertRaises(OSError):
                m.operate(self.base, "install", self.candidate, True, wsi_library=self.bridge)
        self.assertEqual(self.lib.read_bytes(), b"original-engine")
        self.assertEqual(self.wsi.read_bytes(), b"original-wsi")
        self.assertEqual((self.directory / "original.dylib").read_bytes(), b"original-engine")
        m.operate(self.base, "install", self.candidate, True, wsi_library=self.bridge)
        m.operate(self.base, "verify")

    def test_moltenvk_only_install_refused(self):
        with self.assertRaisesRegex(ValueError, "wsi-library"):
            m.operate(self.base, "install", self.candidate, True)
        self.assertFalse(self.directory.exists())

    def test_second_file_failure_restores_first_file(self):
        real = m.replace_file
        def fail_host(src, dst, expected):
            if Path(dst) == self.lib:
                raise OSError("injected host publication failure")
            return real(src, dst, expected)
        with mock.patch.object(m, "replace_file", side_effect=fail_host):
            with self.assertRaises(OSError):
                m.operate(self.base, "install", self.candidate, True, wsi_library=self.bridge)
        self.assertEqual(self.lib.read_bytes(), b"original-engine")
        self.assertEqual(self.wsi.read_bytes(), b"original-wsi")
        m.operate(self.base, "install", self.candidate, True, wsi_library=self.bridge)
        m.operate(self.base, "verify")

    def test_wsi_drift_and_corrupted_backup_refused(self):
        m.operate(self.base, "install", self.candidate, True, wsi_library=self.bridge)
        self.wsi.write_bytes(b"unknown")
        with self.assertRaises(ValueError):
            m.operate(self.base, "rollback", apply=True)
        self.wsi.write_bytes(self.bridge.read_bytes())
        (self.directory / "original-win32u.so").write_bytes(b"bad")
        with self.assertRaises(ValueError):
            m.operate(self.base, "verify")

    def test_withdrawn_candidate_cannot_be_reinstalled(self):
        with mock.patch.object(m, "WITHDRAWN_SHA256", {m.adapter.sha(self.candidate)}):
            with self.assertRaisesRegex(ValueError, "withdrawn"):
                m.operate(self.base, "install", self.candidate, True, wsi_library=self.bridge)
        self.assertFalse(self.directory.exists())
        self.assertEqual(self.lib.read_bytes(), b"original-engine")
        self.assertEqual(self.wsi.read_bytes(), b"original-wsi")


if __name__ == "__main__":
    unittest.main()
