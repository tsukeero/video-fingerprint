// Runs under `node --test test/` and `deno test -A test/`.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, unlinkSync, openAsBlob } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { blake3 } from '@noble/hashes/blake3.js';
import { utf8ToBytes } from '@noble/hashes/utils.js';
import { CHUNK, fingerprintBlob, fingerprintWith, ranges } from '../index.js';
import { fingerprintPath } from '../path.js';

const vectors = JSON.parse(readFileSync(new URL('../../vectors/vectors.json', import.meta.url), 'utf8')).vectors;

/** Test content per SPEC.md: 64 KiB blocks, block i = BLAKE3 XOF(name || u64le(i))[:65536]. */
function contentReader(name) {
  const prefix = utf8ToBytes(name);
  const input = new Uint8Array(prefix.length + 8);
  input.set(prefix);
  const view = new DataView(input.buffer);
  return (off, n) => {
    const out = new Uint8Array(n);
    let done = 0;
    while (done < n) {
      const pos = off + BigInt(done);
      const i = pos / BigInt(CHUNK);
      const r = Number(pos % BigInt(CHUNK));
      view.setBigUint64(prefix.length, i, true);
      const block = blake3(input, { dkLen: CHUNK });
      const take = Math.min(CHUNK - r, n - done);
      out.set(block.subarray(r, r + take), done);
      done += take;
    }
    return out;
  };
}

test('all vectors match', async () => {
  assert.ok(vectors.length >= 10);
  for (const v of vectors) {
    assert.equal(await fingerprintWith(BigInt(v.size), contentReader(v.name)), v.fingerprint, v.name);
  }
});

test('file path, Blob and callback agree', async () => {
  const name = 'file-roundtrip';
  const size = 5 * CHUNK + 123;
  const data = contentReader(name)(0n, size);
  const path = join(tmpdir(), `vfp-js-test-${Date.now()}.bin`);
  writeFileSync(path, data);
  try {
    const want = await fingerprintWith(size, contentReader(name));
    assert.equal(await fingerprintPath(path), want, 'fingerprintPath');
    assert.equal(await fingerprintBlob(new Blob([data])), want, 'fingerprintBlob(in-memory Blob)');
    if (typeof openAsBlob === 'function') {
      assert.equal(await fingerprintBlob(await openAsBlob(path)), want, 'fingerprintBlob(fs.openAsBlob)');
    }
  } finally {
    unlinkSync(path);
  }
});

test('short read is an error', async () => {
  await assert.rejects(fingerprintWith(10 * CHUNK, (off, n) => (off > 0n ? new Uint8Array(0) : new Uint8Array(n))));
});

test('ranges are disjoint above the whole-file threshold', () => {
  const C = BigInt(CHUNK);
  for (const size of [3n * C + 1n, 3n * C + 2n, 4n * C, 7n * C + 5n, (1n << 64n) - 1n]) {
    const r = ranges(size);
    assert.equal(r.length, 3);
    assert.ok(r[0][0] + r[0][1] <= r[1][0]);
    assert.ok(r[1][0] + r[1][1] <= r[2][0]);
    assert.equal(r[2][0] + r[2][1], size);
  }
  assert.deepEqual(ranges(3 * CHUNK), [[0n, 3n * C]]);
});

test('format', async () => {
  const fp = await fingerprintWith(0, () => new Uint8Array(0));
  assert.match(fp, /^fp1:[0-9a-f]{32}$/);
});
