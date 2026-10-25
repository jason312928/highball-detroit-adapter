"""EXE transaction tests use synthetic bytes; no game or Wine is launched."""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import blur_workaround as m


class BlurTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.original = b"MZ-fixture" + m.PATTERN + b"fixture-end"
        self.offset = len(b"MZ-fixture")
        self.patched = self.original[:self.offset] + b"\x7f" + self.original[self.offset + 1:]
        for name, value in (("ORIGINAL", m.digest(self.original)), ("PATCHED", m.digest(self.patched)), ("OFFSET", self.offset)):
            p = mock.patch.object(m, name, value)
            p.start()
            self.addCleanup(p.stop)
        for target in m.adapter.targets(self.base):
            target.mkdir(parents=True)
            m.adapter.save(target / m.adapter.OWNER, {"token": "fixture"})
        self.exe = m.adapter.targets(self.base)[1] / m.GAME
        self.exe.parent.mkdir(parents=True)
        self.exe.write_bytes(self.original)
        self.exe.chmod(0o755)
        state = m.adapter.state_dir(self.base)
        state.mkdir()
        self.journal = {"token": "fixture", "status": "installed", "source_exe_sha256": m.ORIGINAL}
        m.adapter.save(state / "transaction.json", self.journal)
        self.backups = state / "blur-workaround"
        guard = mock.patch.object(m, "game_stopped")
        self.stopped = guard.start()
        self.addCleanup(guard.stop)
        out = contextlib.redirect_stdout(io.StringIO())
        out.__enter__()
        self.addCleanup(out.__exit__, None, None, None)

    def test_dry_run_writes_nothing(self):
        m.operate(self.base, "apply")
        self.assertEqual(self.exe.read_bytes(), self.original)
        self.assertFalse(self.backups.exists())

    def test_apply_verify_repeat_rollback_preserves_original_backup(self):
        m.operate(self.base, "apply", True)
        self.assertEqual(self.exe.read_bytes(), self.patched)
        self.assertEqual(self.exe.stat().st_mode & 0o777, 0o755)
        m.operate(self.base, "verify")
        m.operate(self.base, "apply", True)
        m.operate(self.base, "rollback", True)
        m.operate(self.base, "rollback", True)
        self.assertEqual(self.exe.read_bytes(), self.original)
        self.assertEqual((self.backups / "original.exe").read_bytes(), self.original)
        self.assertEqual(m.adapter.read(m.adapter.state_dir(self.base) / "transaction.json"), self.journal)

    def test_unknown_version_refused(self):
        self.exe.write_bytes(self.original + b"changed")
        with self.assertRaises(ValueError):
            m.operate(self.base, "apply", True)
        self.assertFalse(self.backups.exists())

    def test_corrupted_backup_refuses_verify_and_rollback(self):
        m.operate(self.base, "apply", True)
        (self.backups / "original.exe").write_bytes(b"bad")
        for action in ("verify", "rollback"):
            with self.assertRaises(ValueError):
                m.operate(self.base, action, True)
        self.assertEqual(self.exe.read_bytes(), self.patched)

    def test_unrecorded_patch_refused(self):
        self.exe.write_bytes(self.patched)
        with self.assertRaises((ValueError, FileNotFoundError)):
            m.operate(self.base, "verify")

    def test_running_game_refused(self):
        self.stopped.side_effect = ValueError("Game running")
        with self.assertRaises(ValueError):
            m.operate(self.base, "apply", True)
        self.assertFalse(self.backups.exists())

    def test_changed_game_not_overwritten_during_rollback(self):
        m.operate(self.base, "apply", True)
        changed = self.patched + b"update"
        self.exe.write_bytes(changed)
        with self.assertRaises(ValueError):
            m.operate(self.base, "rollback", True)
        self.assertEqual(self.exe.read_bytes(), changed)

    def test_failed_atomic_publish_retains_recoverable_backup(self):
        publish = m.os.replace
        def fail_game(src, dst):
            if Path(dst) == self.exe:
                raise OSError("injected publish failure")
            return publish(src, dst)
        with mock.patch.object(m.os, "replace", side_effect=fail_game):
            with self.assertRaises(OSError):
                m.operate(self.base, "apply", True)
        self.assertEqual(self.exe.read_bytes(), self.original)
        self.assertEqual((self.backups / "original.exe").read_bytes(), self.original)
        m.operate(self.base, "apply", True)
        self.assertEqual(self.exe.read_bytes(), self.patched)

    def test_symlink_backup_directory_refused(self):
        self.backups.symlink_to(self.exe.parent, target_is_directory=True)
        with self.assertRaises(ValueError):
            m.operate(self.base, "apply", True)


if __name__ == "__main__":
    unittest.main()
