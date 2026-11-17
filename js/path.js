// File-path helper for server runtimes: Node, Deno (node: compat) and Bun.
// Kept out of index.js so browser bundles never see `node:fs`.
import { open } from 'node:fs/promises';
import { fingerprintWith } from './index.js';

/**
 * Fingerprint of a file on disk. The size is taken once, at open time.
 * @param {string | URL} path
 * @returns {Promise<string>}
 */
export async function fingerprintPath(path) {
  const fh = await open(path, 'r');
  try {
    const { size } = await fh.stat({ bigint: true });
    return await fingerprintWith(size, async (off, n) => {
      const buf = new Uint8Array(n);
      let got = 0;
      while (got < n) {
        const { bytesRead } = await fh.read(buf, got, n - got, Number(off) + got);
        if (bytesRead === 0) break;
        got += bytesRead;
      }
      return got === n ? buf : buf.subarray(0, got);
    });
  } finally {
    await fh.close();
  }
}
