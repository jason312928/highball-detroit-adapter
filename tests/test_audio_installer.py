"""Audio transactions use synthetic DLL bytes and a temporary Highball layout."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock


class AudioInstallerTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location(
            "audiofix_under_test",
            Path(__file__).resolve().parents[1] / "audio/audiofix.py",
        )
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.temp = tempfile.TemporaryDirectory(
            prefix="Detroit audio path with spaces "
        )
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = self.root / "Highball data"
        self.kit = self.root / "Audio kit"
        self.kit.mkdir()
        self.old = b"synthetic original audio library"
        header = bytearray(512)
        header[:2] = b"MZ"
        struct.pack_into("<I", header, 0x3C, 0x80)
        header[0x80:0x84] = b"PE\0\0"
        struct.pack_into("<H", header, 0x84, 0x8664)
        self.new = bytes(header) + b"Wine builtin DLL\0HB_DETROIT_AUDIO_V1\0"
        (self.kit / "xaudio2_8.dll").write_bytes(self.new)
        self.m.KIT = self.kit
        self.m.OLD = self.m.sha(self._write(self.root / "old.fixture", self.old))
        self.m.NEW = self.m.sha(self.kit / "xaudio2_8.dll")
        for rel in self.m.RELS:
            self._write(self.base / rel, self.old)
        for rel in ("engines/detroit-strict-003-r28", "bottles/Detroit Isolated"):
            self._write(
                self.base / rel / ".detroit-adapter-owner.json", b'{"token":"fixture"}'
            )
        self._write(
            self.base / "bottles/Detroit Isolated/bottle.json",
            b'{"engineID":"detroit-strict-003-r28"}',
        )
        self._write(
            self.base / ".detroit-adapter/transaction.json",
            b'{"status":"installed","token":"fixture"}',
        )
        self.state = self.base / ".detroit-adapter/audio-v1"
        self.quiet = mock.patch.object(self.m, "quiet")
        self.quiet.start()
        self.addCleanup(self.quiet.stop)

    @staticmethod
    def _write(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def invoke(self, operation, mode="--apply"):
        args = ["audiofix.py", operation, "--highball-root", str(self.base), mode]
        with (
            mock.patch.object(sys, "argv", args),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.m.main()

    def assert_libraries(self, expected):
        for rel in self.m.RELS:
            self.assertEqual((self.base / rel).read_bytes(), expected)

    def test_dry_run_does_not_create_transaction_or_replace_libraries(self):
        self.invoke("install", "--dry-run")
        self.assertFalse(self.state.exists())
        self.assert_libraries(self.old)

    def test_install_verify_repeat_and_rollback(self):
        self.invoke("install")
        self.invoke("verify", "--dry-run")
        self.invoke("install")
        self.assert_libraries(self.new)
        self.invoke("rollback")
        self.invoke("rollback")
        self.assert_libraries(self.old)

    def test_second_write_failure_restores_both_originals(self):
        real = self.m.copy_atomic
        calls = 0

        def fail_once(src, dst):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("Injected failure after the first DLL was replaced")
            return real(src, dst)

        with mock.patch.object(self.m, "copy_atomic", side_effect=fail_once):
            with self.assertRaises(OSError):
                self.invoke("install")
        self.assert_libraries(self.old)
        self.invoke("install")
        self.assert_libraries(self.new)

    def test_interrupted_mixed_state_recovers_before_reinstall(self):
        self.invoke("install")
        self.invoke("rollback")
        journal = self.m.read(self.state / "transaction.json")
        journal["status"] = "installing"
        self.m.save(self.state / "transaction.json", journal)
        (self.base / self.m.RELS[0]).write_bytes(self.new)
        self.invoke("install", "--dry-run")
        self.assertEqual((self.base / self.m.RELS[0]).read_bytes(), self.new)
        self.invoke("install")
        self.assert_libraries(self.new)

    def test_conflict_in_second_library_prevents_partial_rollback(self):
        self.invoke("install")
        (self.base / self.m.RELS[1]).write_bytes(b"newer independent replacement")
        with self.assertRaises(ValueError):
            self.invoke("rollback")
        self.assertEqual((self.base / self.m.RELS[0]).read_bytes(), self.new)
        self.assertEqual(
            (self.base / self.m.RELS[1]).read_bytes(), b"newer independent replacement"
        )

    def test_candidate_hash_and_architecture_are_checked(self):
        path = self.kit / "xaudio2_8.dll"
        path.write_bytes(b"corrupt")
        with self.assertRaises(ValueError):
            self.invoke("install")
        damaged = bytearray(self.new)
        struct.pack_into("<H", damaged, 0x84, 0xAA64)
        path.write_bytes(damaged)
        self.m.NEW = self.m.sha(path)
        with self.assertRaises(ValueError):
            self.invoke("install")
        self.assert_libraries(self.old)

    def test_ownership_mismatch_is_rejected(self):
        owner = self.base / "bottles/Detroit Isolated/.detroit-adapter-owner.json"
        owner.write_text(json.dumps({"token": "unrelated"}))
        with self.assertRaises(ValueError):
            self.invoke("install")
        self.assert_libraries(self.old)
