"""Tool preparation uses temporary layouts, with no Wine or current user data."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prepare_metal as m


class PrepareMetalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="Private Metal spaces ")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        (self.base / "engines").mkdir(); (self.base / "bottles").mkdir()
        self.state = self.base / ".detroit-adapter"
        self.lock = json.loads((m.KIT / "metal-toolchain-lock.json").read_text())
        self.args = argparse.Namespace(highball_root=self.base, verify=False,
                                       rollback=False, apply=False, archive=None)

    def test_dry_run_makes_no_state_and_downloads_nothing(self):
        with mock.patch.object(m, "download_or_copy") as download, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(m.execute(self.args), 0)
        download.assert_not_called()
        self.assertFalse(self.state.exists())

    def test_corrupt_archive_rejected(self):
        source = self.base / "source.aar"; source.write_bytes(b"bad archive")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            m.download_or_copy(source, self.base / "copy.aar", self.lock)

    def test_extract_failure_removes_only_own_stage(self):
        self.state.mkdir()
        sentinel = self.base / "engines/keep"; sentinel.write_text("original")
        with mock.patch.object(m, "download_or_copy"), mock.patch.object(m, "run", side_effect=RuntimeError("extract failure")):
            with self.assertRaisesRegex(RuntimeError, "extract failure"):
                m.prepare(self.base, None, self.lock)
        self.assertEqual(list(self.state.iterdir()), [])
        self.assertEqual(sentinel.read_text(), "original")

    def test_existing_unknown_tools_are_not_overwritten(self):
        target = self.state / "tools"; target.mkdir(parents=True)
        (target / "provenance.json").write_text('{}')
        self.args.apply = True
        with self.assertRaisesRegex(ValueError, "different provenance"):
            m.execute(self.args)
        self.assertEqual((target / "provenance.json").read_text(), '{}')

    def test_repeat_install_and_reversible_repeat_rollback(self):
        target = self.state / "tools"; target.mkdir(parents=True)
        (target / "fixture").write_text("retained compiler")
        self.args.apply = True
        with mock.patch.object(m, "check_tools", return_value=target / m.COMPILER), mock.patch.object(m, "prepare") as prepare, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(m.execute(self.args), 0)
            prepare.assert_not_called()
            self.args.rollback = True
            self.assertEqual(m.execute(self.args), 0)
            self.assertEqual(m.execute(self.args), 0)
        archived = list(self.state.glob("tools-archived-*"))
        self.assertEqual(len(archived), 1)
        self.assertEqual((archived[0] / "fixture").read_text(), "retained compiler")
