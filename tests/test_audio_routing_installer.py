"""Routing transactions: interrupted writes, rollback, settings and ownership."""

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


class RoutingInstallerTests(unittest.TestCase):
    def setUp(self):
        audio = Path(__file__).resolve().parents[1] / "audio"
        with mock.patch.object(sys, "path", [str(audio)] + sys.path):
            spec = importlib.util.spec_from_file_location("routing_under_test", audio / "routingfix.py")
            self.m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.m)
        self.tmp = tempfile.TemporaryDirectory(prefix="routing path with spaces ")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name) / "Highball"
        self.kit = Path(self.tmp.name) / "routing bundle"
        self.kit.mkdir()
        self.m.KIT = self.kit
        self.old = b"fixture original audio"
        self.new = {}
        bundle = {"version": 2, "files": {}}
        for index, name in enumerate(["xaudio2_8.dll", "mmdevapi.dll"]):
            data = bytearray(512)
            data[:2] = b"MZ"
            struct.pack_into("<I", data, 60, 128)
            data[128:134] = b"PE\0\0\x64\x86"
            data += b"Wine builtin DLL\0HB_DETROIT_AUDIO_V2\0" + bytes([index])
            self.new[name] = bytes(data)
            (self.kit / name).write_bytes(data)
            old_path = self.kit / (name + ".before")
            old_path.write_bytes(self.old)
            bundle["files"][name] = {"sha256": self.m.audiofix.sha(self.kit / name),
                "accepted_previous_sha256": [self.m.audiofix.sha(old_path)]}
            for directory in self.m.DIRS:
                self.write(self.base / directory / name, self.old)
        self.write(self.kit / "manifest.json", json.dumps(bundle).encode())
        for rel in ["engines/detroit-strict-003-r28", "bottles/Detroit Isolated"]:
            self.write(self.base / rel / ".detroit-adapter-owner.json", b'{"token":"fixture"}')
        self.write(self.base / ".detroit-adapter/transaction.json", b'{"status":"installed","token":"fixture"}')
        self.write(self.base / self.m.SETTINGS,
                   b'{"engineID":"detroit-strict-003-r28","environment":{"KEEP":"yes"}}')
        self.quiet = mock.patch.object(self.m.audiofix, "quiet")
        self.quiet.start()
        self.addCleanup(self.quiet.stop)

    @staticmethod
    def write(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def invoke(self, op, mode="--apply"):
        with mock.patch.object(sys, "argv", ["routingfix.py", op, "--highball-root", str(self.base), mode]), contextlib.redirect_stdout(io.StringIO()):
            self.m.main()

    def assert_files(self, installed):
        for directory in self.m.DIRS:
            for name in self.new:
                self.assertEqual((self.base / directory / name).read_bytes(), self.new[name] if installed else self.old)

    def test_dry_run_keeps_everything_unchanged(self):
        self.invoke("install", "--dry-run")
        self.assert_files(False)
        self.assertFalse((self.base / self.m.STATE).exists())

    def test_install_verify_repeat_and_rollback_preserves_other_settings(self):
        self.invoke("install")
        self.invoke("verify")
        self.invoke("install")
        self.assert_files(True)
        settings = self.m.audiofix.read(self.base / self.m.SETTINGS)
        settings["environment"]["LATER"] = "keep"
        self.m.audiofix.save(self.base / self.m.SETTINGS, settings)
        self.invoke("rollback")
        self.invoke("rollback")
        self.assert_files(False)
        self.assertEqual(self.m.audiofix.read(self.base / self.m.SETTINGS)["environment"], {"KEEP": "yes", "LATER": "keep"})

    def test_partial_write_failure_restores_all_four_files(self):
        real = self.m.audiofix.copy_atomic
        calls = 0
        def failing(src, dst):
            nonlocal calls
            calls += 1
            if calls == 4:
                raise OSError("injected disk failure")
            real(src, dst)
        with mock.patch.object(self.m.audiofix, "copy_atomic", failing), self.assertRaises(OSError):
            self.invoke("install")
        self.assert_files(False)
        self.assertFalse(self.m.env_value(self.base)["present"])

    def test_rollback_rejects_a_modified_dll(self):
        self.invoke("install")
        p = self.base / self.m.DIRS[0] / "mmdevapi.dll"
        p.write_bytes(b"user replacement")
        with self.assertRaisesRegex(ValueError, "changed after"):
            self.invoke("rollback")
        self.assertEqual(p.read_bytes(), b"user replacement")

    def test_rollback_rejects_changed_routing_preference(self):
        self.invoke("install")
        settings = self.m.audiofix.read(self.base / self.m.SETTINGS)
        settings["environment"][self.m.KEY] = "0"
        self.m.audiofix.save(self.base / self.m.SETTINGS, settings)
        with self.assertRaisesRegex(ValueError, "setting changed"):
            self.invoke("rollback")
        self.assert_files(True)

    def test_unreviewed_original_rejected_before_writes(self):
        p = self.base / self.m.DIRS[0] / "mmdevapi.dll"
        p.write_bytes(b"unknown")
        with self.assertRaisesRegex(ValueError, "Unreviewed"):
            self.invoke("install")
        self.assertFalse((self.base / self.m.STATE / "transaction.json").exists())

    def test_interrupted_transaction_recovers_before_reinstall(self):
        self.invoke("install")
        state = self.base / self.m.STATE
        journal = self.m.audiofix.read(state / "transaction.json")
        journal["status"] = "installing"
        self.m.audiofix.save(state / "transaction.json", journal)
        self.invoke("install")
        self.invoke("verify")
        self.assert_files(True)

    def test_journal_cannot_redirect_rollback_outside_private_paths(self):
        self.invoke("install")
        state = self.base / self.m.STATE
        journal = self.m.audiofix.read(state / "transaction.json")
        journal["entries"][0]["path"] = "../outside.dll"
        self.m.audiofix.save(state / "transaction.json", journal)
        with self.assertRaisesRegex(ValueError, "reviewed bundle"):
            self.invoke("rollback")
        self.assert_files(True)
