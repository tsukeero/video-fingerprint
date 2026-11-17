"""fp1 quick fingerprint for large video files. See ../SPEC.md."""
import os
from typing import Callable, List, Tuple

from blake3 import blake3

CHUNK = 65536
CONTEXT = "video-fingerprint 2026-11-17 fp1"
PREFIX = "fp1:"

__all__ = ["CHUNK", "CONTEXT", "PREFIX", "ranges", "fingerprint_with", "fingerprint_file"]


def ranges(size: int) -> List[Tuple[int, int]]:
    """(offset, length) ranges fp1 hashes for a file of `size` bytes, in hashing order."""
    if size <= 3 * CHUNK:
        return [(0, size)]
    mid = (size - CHUNK) // 2
    return [(0, CHUNK), (mid, CHUNK), (size - CHUNK, CHUNK)]


def fingerprint_with(size: int, read_at: Callable[[int, int], bytes]) -> str:
    """Fingerprint from a size and `read_at(offset, n)` returning exactly n bytes."""
    if not 0 <= size < 1 << 64:
        raise ValueError(f"size out of range: {size}")
    h = blake3(derive_key_context=CONTEXT)
    h.update(size.to_bytes(8, "little"))
    for off, length in ranges(size):
        done = 0
        while done < length:
            n = min(CHUNK, length - done)
            b = read_at(off + done, n)
            if len(b) != n:
                raise EOFError(f"short read at {off + done}: wanted {n}, got {len(b)}")
            h.update(b)
            done += n
    return PREFIX + h.digest(length=16).hex()


def fingerprint_file(path) -> str:
    """Fingerprint of a file on disk. The size is taken once, at open time."""
    with open(path, "rb") as f:
        size = os.fstat(f.fileno()).st_size

        def read_at(off: int, n: int) -> bytes:
            f.seek(off)
            return f.read(n)

        return fingerprint_with(size, read_at)
