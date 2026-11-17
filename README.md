# video-fingerprint

Quick, stable identity for large video files: file size plus three sampled 64 KiB chunks,
hashed with BLAKE3 → `fp1:<32 hex>`. About three small reads per file regardless of size;
survives renames and moves. Used to key thumbnails and metadata shared between the media
viewer and the metadata processor.

The definition is in [SPEC.md](SPEC.md). Implementations must pass `vectors/vectors.json`.

| Dir | What |
|---|---|
| `rust/` | crate `video-fingerprint` + CLI `vfp FILE...` |
| `python/` | package `video_fingerprint` + `python -m video_fingerprint FILE...` |
| `vectors/` | shared test vectors and their generator |

## Tests

```sh
cd rust && cargo test
python -m venv .venv && .venv/Scripts/python -m pip install -e python   # bin/ on Linux
.venv/Scripts/python -m unittest discover -s python/tests
```

`vectors/generate.py` writes `vectors.json` from the Python implementation; the Rust tests
check the same file, so the two cross-check each other. Existing fp1 vectors must never change.
