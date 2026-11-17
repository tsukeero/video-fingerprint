# video-fingerprint: specification

Version: **fp1**. Status: draft (2026-11-17).

A quick, stable identity for large video files. It reads only three 64 KiB pieces of a file, so
fingerprinting a library of 100k+ videos costs about three small reads per file, not reading
every byte. It is used to key thumbnails and metadata so they survive renames and moves.

## Definition (fp1)

Constants:

- `CHUNK = 65536` (64 KiB)
- `CONTEXT = "video-fingerprint 2026-11-17 fp1"` (BLAKE3 key-derivation context string, ASCII)

Input: the file's length `size` in bytes (taken once, when the file is opened) and its content.

1. Create a BLAKE3 hasher in **key derivation mode** with `CONTEXT`
   (`blake3::Hasher::new_derive_key(CONTEXT)` in Rust, `blake3(derive_key_context=CONTEXT)` in Python).
2. Feed `size` as an unsigned 64-bit **little-endian** integer (8 bytes).
3. Feed the content:
   - If `size <= 3 * CHUNK` (196 608 bytes): the **whole file**, bytes `[0, size)`.
   - Otherwise these three ranges, in this order:
     - start:  `[0, CHUNK)`
     - middle: `[mid, mid + CHUNK)` where `mid = floor((size - CHUNK) / 2)`
     - end:    `[size - CHUNK, size)`

     For `size > 3 * CHUNK` the three ranges never overlap.
4. Take the first **16 bytes** (128 bits) of the hash output.
5. Format as `fp1:` followed by 32 **lowercase hex** digits.

Example shape: `fp1:3f0c9a…` (36 characters total).

Errors: if a read returns fewer bytes than the range needs (the file shrank or is unreadable),
the fingerprint is an error. Never pad, never hash a partial range.

## Properties

- **Cost:** 1 read for files up to 192 KiB, otherwise 3 reads of 64 KiB, regardless of file size.
- **Stable under:** rename, move, copy, different mount points, different machines.
- **Changes when:** the file size changes, or any byte inside the three sampled ranges changes
  (re-mux, tag edits, header rewrites). Byte changes outside the ranges are not detected; this is
  an identity, not an integrity check.
- **Collisions:** accidental collisions need equal size **and** identical sampled bytes. Container
  headers (random segment UIDs in MKV, mux dates, titles) and trailing indexes (MKV Cues, MP4 moov)
  make that practically impossible for distinct encodes, including episodes of the same length
  with identical openings. With 128 bits of output, a hash-level collision among 10^6 files has
  probability below 10^-26. Byte-identical copies share a fingerprint by design.
- **Why key derivation mode:** the context string domain-separates fp1 from plain BLAKE3 of the
  same bytes and from future versions.

## Versioning

The `fp1:` prefix names this exact definition. Any change (chunk size, positions, hash, output
length) gets a new prefix (`fp2:` …); consumers store the full prefixed string and never compare
fingerprints of different versions.

## Test vectors

`vectors/vectors.json` lists `{ "name", "size", "fingerprint" }`. Test content is not stored;
it is generated so any language with BLAKE3 can reproduce it, including multi-terabyte cases:

> The content of vector `name` is the BLAKE3 **extendable output** (XOF) of the UTF-8 bytes of
> `name` (plain hash mode, no key), bytes `[0, size)`. Byte at offset `o` is XOF output position `o`.

Implementations must pass every vector. Implementations should expose a function that takes
`size` and a "read `n` bytes at offset `o`" callback, so large vectors can be tested without files.
