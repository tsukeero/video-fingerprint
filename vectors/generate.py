"""Regenerate vectors.json from the Python implementation.

    python vectors/generate.py   (with the python/ package importable and blake3 installed)

The Rust tests then check the same file, so the two implementations cross-check each other.
Only regenerate when adding vectors; existing fingerprints must never change for fp1.
"""
import json
import sys
from pathlib import Path

from blake3 import blake3

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
from video_fingerprint import CHUNK, fingerprint_with  # noqa: E402

C = CHUNK
SIZES = {
    "empty": 0,
    "one-byte": 1,
    "chunk-minus-1": C - 1,
    "chunk": C,
    "chunk-plus-1": C + 1,
    "whole-file-max": 3 * C,         # last size hashed whole
    "sampled-min": 3 * C + 1,        # first size sampled (middle starts at C)
    "sampled-min-plus-1": 3 * C + 2,
    "odd-size": 1_000_003,
    "ten-mib": 10 * 1024 * 1024,
    "over-4gib": (1 << 32) + 12345,  # 32-bit size overflow
    "one-tib": 1 << 40,
    "u64-max": (1 << 64) - 1,        # largest representable size
}


BLOCK = 65536


def content_reader(name):
    """Test content per SPEC.md: 64 KiB blocks, block i = BLAKE3 XOF(name || u64le(i))[:65536]."""
    prefix = name.encode()

    def block(i):
        return blake3(prefix + i.to_bytes(8, "little")).digest(length=BLOCK)

    def read_at(off, n):
        out = bytearray()
        while len(out) < n:
            i, r = divmod(off + len(out), BLOCK)
            out += block(i)[r:r + n - len(out)]
        return bytes(out)

    return read_at


def main():
    vectors = [{"name": n, "size": str(s), "fingerprint": fingerprint_with(s, content_reader(n))} for n, s in SIZES.items()]
    doc = {
        "note": "size is a decimal string: 2^64-1 does not fit a JSON number in every language",
        "version": "fp1",
        "content": "64 KiB blocks; block i = first 65536 bytes of BLAKE3 XOF (plain hash) of UTF-8 name + u64le(i)",
        "vectors": vectors,
    }
    out = Path(__file__).with_name("vectors.json")
    out.write_text(json.dumps(doc, indent=2) + "\n", newline="\n")
    for v in vectors:
        print(f'{v["fingerprint"]}  {v["name"]} ({v["size"]})')


if __name__ == "__main__":
    main()
