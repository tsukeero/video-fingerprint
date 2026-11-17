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


def content_reader(name):
    h = blake3(name.encode())
    return lambda off, n: h.digest(length=n, seek=off)


def main():
    vectors = [{"name": n, "size": s, "fingerprint": fingerprint_with(s, content_reader(n))} for n, s in SIZES.items()]
    doc = {
        "version": "fp1",
        "content": "BLAKE3 XOF (plain hash mode) of the UTF-8 name; byte at offset o = XOF position o",
        "vectors": vectors,
    }
    out = Path(__file__).with_name("vectors.json")
    out.write_text(json.dumps(doc, indent=2) + "\n", newline="\n")
    for v in vectors:
        print(f'{v["fingerprint"]}  {v["name"]} ({v["size"]})')


if __name__ == "__main__":
    main()
