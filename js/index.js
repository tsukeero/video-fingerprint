// fp1 quick fingerprint for large video files. See ../SPEC.md.
// Runtime-neutral: works in browsers, Node, Deno and Bun. File-path helper is in ./path.js.
import { blake3 } from '@noble/hashes/blake3.js';
import { bytesToHex, utf8ToBytes } from '@noble/hashes/utils.js';

export const CHUNK = 65536;
export const CONTEXT = 'video-fingerprint 2026-11-17 fp1';
export const PREFIX = 'fp1:';

const C = BigInt(CHUNK);
const U64_MAX = (1n << 64n) - 1n;
const CONTEXT_BYTES = utf8ToBytes(CONTEXT);

/**
 * Byte ranges fp1 hashes for a file of `size` bytes, in hashing order.
 * @param {number | bigint} size
 * @returns {Array<[bigint, bigint]>} [offset, length] pairs
 */
export function ranges(size) {
  const s = BigInt(size);
  if (s < 0n || s > U64_MAX) throw new RangeError(`size out of range: ${s}`);
  if (s <= 3n * C) return [[0n, s]];
  const mid = (s - C) / 2n; // BigInt division floors for non-negative values
  return [[0n, C], [mid, C], [s - C, C]];
}

/**
 * Fingerprint from a size and a reader. `readAt(offset, length)` must resolve to exactly
 * `length` bytes; anything shorter is an error.
 * @param {number | bigint} size
 * @param {(offset: bigint, length: number) => Uint8Array | Promise<Uint8Array>} readAt
 * @returns {Promise<string>}
 */
export async function fingerprintWith(size, readAt) {
  const s = BigInt(size);
  const h = blake3.create({ context: CONTEXT_BYTES, dkLen: 16 });
  const sizeLE = new Uint8Array(8);
  new DataView(sizeLE.buffer).setBigUint64(0, s, true);
  h.update(sizeLE);
  for (const [off, len] of ranges(s)) {
    for (let done = 0n; done < len; ) {
      const n = len - done < C ? len - done : C;
      const pos = off + done;
      const b = await readAt(pos, Number(n));
      if (!(b instanceof Uint8Array) || b.length !== Number(n)) {
        throw new Error(`short read at ${pos}: wanted ${n}, got ${b?.length}`);
      }
      h.update(b);
      done += n;
    }
  }
  return PREFIX + bytesToHex(h.digest());
}

/**
 * Fingerprint of any Blob: a browser File (input, drag-drop, File System Access API),
 * `Bun.file(path)`, or Node's `fs.openAsBlob(path)`. Only the sampled ranges are read.
 * @param {Blob} blob
 * @returns {Promise<string>}
 */
export function fingerprintBlob(blob) {
  return fingerprintWith(blob.size, async (off, n) => {
    const start = Number(off);
    return new Uint8Array(await blob.slice(start, start + n).arrayBuffer());
  });
}
