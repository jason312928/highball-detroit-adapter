#!/usr/bin/env python3
"""Read-only Detroit ShaderCode.bin inspection. Extracts a few local diagnostic modules."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("cache", type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--max-matches", type=int, default=3)
    a = p.parse_args()
    if not 1 <= a.max_matches <= 100:
        p.error("max-matches must be between 1 and 100")
    if a.output.exists():
        p.error("output must be a new directory, to preserve previous evidence")
    a.output.mkdir(parents=True)
    records = 0; matches = []
    with a.cache.open("rb") as f:
        while True:
            pos = f.tell(); header = f.read(4)
            if not header: break
            if len(header) != 4: raise ValueError("truncated record header")
            n = struct.unpack("<I", header)[0]
            if not 0 < n < 64 * 1024 * 1024: raise ValueError(f"unsupported record at {pos}")
            compressed = f.read(n)
            if len(compressed) != n: raise ValueError("truncated compressed record")
            z = zlib.decompressobj()
            data = z.decompress(compressed, 64 * 1024 * 1024)
            if not z.eof or z.unused_data: raise ValueError("unsupported zlib framing or oversized shader")
            records += 1
            if b"vfMsBindPosePosition" not in data: continue
            offset = data.find(bytes.fromhex("03022307"))
            if offset < 0 or (len(data) - offset) % 4: continue
            binary = data[offset:]; words = struct.unpack("<" + "I" * (len(binary) // 4), binary)
            if len(words) < 5 or words[4] != 0: continue
            i = 5; stage = None
            while i < len(words):
                count, op = words[i] >> 16, words[i] & 65535
                if not count or i + count > len(words): break
                if op == 15: stage = words[i + 1]
                i += count
            if i != len(words) or stage != 0: continue
            name = f"vertex-{records}.spv"
            (a.output / name).write_bytes(binary)
            matches.append(dict(record=records, compressed_offset=pos, compressed_bytes=n,
                                spirv_offset=offset, spirv_bytes=len(binary), file=name,
                                sha256=hashlib.sha256(binary).hexdigest()))
            if len(matches) >= a.max_matches: break
    manifest = dict(scanned=records, matches=matches,
                    limitation="Cache modules cannot identify the vertex state of a failed pipeline by themselves.")
    (a.output / "records.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
