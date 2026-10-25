"""Offline compiler selection, atomic failure and repeat runs; no real game data."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "vendor/compile_msl_library_cache.sh"


class CacheCompilerTests(unittest.TestCase):
    def test_explicit_compiler_spaces_metadata_and_repeat(self):
        for jobs in (1, 2):
            with self.subTest(jobs=jobs), tempfile.TemporaryDirectory(prefix="Metal cache spaces ") as tmp:
                root = Path(tmp)
                compiler = root / "fake metal"
                compiler.write_text('#!/bin/bash\nset -eu\nprintf "%s\\n" "$@" >> "$TEST_CALLS"\nwhile [ "$1" != "-o" ]; do shift; done\nshift\nprintf MTLB > "$1"\n')
                compiler.chmod(0o755)
                source = root / "msl-v1-fixture.metal"
                source.write_text("synthetic test input")
                # macOS ships Bash 3.2: -nt compares whole-second timestamps.
                os.utime(source, (946684800, 946684800))
                source.with_suffix(".meta").write_text("fp_fast_math_flags=0\nis_position_invariant=1\n")
                calls = root / "calls.txt"
                env = dict(os.environ, METAL_TOOL=str(compiler), TEST_CALLS=str(calls))
                args = ["/bin/bash", str(SCRIPT), "-j", str(jobs), str(root)]
                first = subprocess.run(args, env=env, text=True, capture_output=True)
                self.assertEqual(first.returncode, 0, first.stderr)
                self.assertEqual(source.with_suffix(".metallib").read_bytes(), b"MTLB")
                self.assertIn("-fmetal-math-mode=safe", calls.read_text())
                self.assertIn("-fpreserve-invariance", calls.read_text())
                before = calls.read_bytes()
                repeat = subprocess.run(args, env=env, text=True, capture_output=True)
                self.assertEqual(repeat.returncode, 0, repeat.stderr)
                self.assertEqual(calls.read_bytes(), before)
                self.assertEqual(source.read_text(), "synthetic test input")

    def test_failure_keeps_existing_cache(self):
        with tempfile.TemporaryDirectory(prefix="Metal failure space ") as tmp:
            root = Path(tmp)
            compiler = root / "failing metal"
            compiler.write_text("#!/bin/bash\nexit 7\n")
            compiler.chmod(0o755)
            source = root / "msl-v1-fixture.metal"
            source.write_text("input")
            binary = source.with_suffix(".metallib")
            binary.write_bytes(b"existing cache")
            result = subprocess.run(["/bin/bash", str(SCRIPT), "--force", str(root)],
                                    env=dict(os.environ, METAL_TOOL=str(compiler)), capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(binary.read_bytes(), b"existing cache")
            self.assertEqual(source.read_text(), "input")

    def test_invalid_explicit_compiler_fails_before_writes(self):
        with tempfile.TemporaryDirectory(prefix="Metal dry space ") as tmp:
            result = subprocess.run(["/bin/bash", str(SCRIPT), tmp],
                                    env=dict(os.environ, METAL_TOOL=tmp + "/missing"), capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("METAL_TOOL", result.stderr)
            self.assertEqual(list(Path(tmp).iterdir()), [])
