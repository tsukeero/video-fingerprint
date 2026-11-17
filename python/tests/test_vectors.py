import json
import os
import tempfile
import unittest
from pathlib import Path

from blake3 import blake3

from video_fingerprint import CHUNK, fingerprint_file, fingerprint_with, ranges

VECTORS = Path(__file__).resolve().parents[2] / "vectors" / "vectors.json"


def content_reader(name):
    """Test content per SPEC.md: BLAKE3 XOF of the vector name, byte o = XOF position o."""
    h = blake3(name.encode())
    return lambda off, n: h.digest(length=n, seek=off)


class Vectors(unittest.TestCase):
    def test_all_vectors_match(self):
        vs = json.loads(VECTORS.read_text())["vectors"]
        self.assertGreaterEqual(len(vs), 10)
        for v in vs:
            with self.subTest(v["name"]):
                self.assertEqual(fingerprint_with(v["size"], content_reader(v["name"])), v["fingerprint"])

    def test_file_matches_callback(self):
        name, size = "file-roundtrip", 5 * CHUNK + 123
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content_reader(name)(0, size))
        try:
            self.assertEqual(fingerprint_file(f.name), fingerprint_with(size, content_reader(name)))
        finally:
            os.unlink(f.name)

    def test_short_read_is_error(self):
        with self.assertRaises(EOFError):
            fingerprint_with(10 * CHUNK, lambda off, n: b"" if off else bytes(n))

    def test_ranges_disjoint_above_threshold(self):
        for size in (3 * CHUNK + 1, 3 * CHUNK + 2, 4 * CHUNK, 7 * CHUNK + 5, (1 << 64) - 1):
            r = ranges(size)
            self.assertEqual(len(r), 3)
            self.assertLessEqual(r[0][0] + r[0][1], r[1][0])
            self.assertLessEqual(r[1][0] + r[1][1], r[2][0])
            self.assertEqual(r[2][0] + r[2][1], size)
        self.assertEqual(ranges(3 * CHUNK), [(0, 3 * CHUNK)])

    def test_format(self):
        fp = fingerprint_with(0, lambda off, n: b"")
        self.assertEqual(len(fp), 36)
        self.assertTrue(fp.startswith("fp1:"))
        self.assertTrue(all(c in "0123456789abcdef" for c in fp[4:]))


if __name__ == "__main__":
    unittest.main()
