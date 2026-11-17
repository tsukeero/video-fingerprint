# video-fingerprint

[![CI](https://github.com/tsukeero/video-fingerprint/actions/workflows/ci.yml/badge.svg)](https://github.com/tsukeero/video-fingerprint/actions/workflows/ci.yml)

Quick, stable identity for large video files: file size plus three sampled 64 KiB chunks,
hashed with BLAKE3 → `fp1:<32 hex>`. About three small reads per file regardless of size;
survives renames and moves. Used to key thumbnails and metadata shared between the media
viewer and the metadata processor.

The definition is in [SPEC.md](SPEC.md). Implementations must pass `vectors/vectors.json`.

| Dir | What |
|---|---|
| `rust/` | crate `video-fingerprint` + CLI `vfp FILE...` |
| `python/` | package `video_fingerprint` + `python -m video_fingerprint FILE...` |
| `js/` | ESM package `video-fingerprint` (browsers, Node, Deno, Bun) + `node js/cli.js FILE...` |
| `vectors/` | shared test vectors and their generator |

## Tests

```sh
cd rust && cargo test
python -m venv .venv && .venv/Scripts/python -m pip install -e python   # bin/ on Linux
.venv/Scripts/python -m unittest discover -s python/tests
cd js && npm install && npm test && npm run test:deno
```

## JavaScript: one API across runtimes

```js
import { fingerprintBlob } from 'video-fingerprint';        // runtime-neutral
import { fingerprintPath } from 'video-fingerprint/path';   // Node, Deno, Bun (node:fs)

await fingerprintBlob(fileFromInputOrDrop);              // browser File
await fingerprintBlob(Bun.file(path));                   // Bun
await fingerprintBlob(await fs.openAsBlob(path));        // Node 20+, Deno 2
await fingerprintPath(path);                             // Node, Deno, Bun
```

A `Blob` is the cross-runtime file type: `slice()` is lazy, so only the three sampled 64 KiB
ranges are read, even for multi-GB files. `fingerprintWith(size, readAt)` takes any async
reader (HTTP range requests, File System Access handles, ...). BLAKE3 is `@noble/hashes`
(pure JS, audited, no native or wasm build).

`vectors/generate.py` writes `vectors.json` from the Python implementation; the Rust tests
check the same file, so the two cross-check each other. Existing fp1 vectors must never change.

## License

[MIT](LICENSE). The same license applies to the Rust, Python and JavaScript implementations, the spec and the test vectors.
