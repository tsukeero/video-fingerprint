export declare const CHUNK: 65536;
export declare const CONTEXT: string;
export declare const PREFIX: 'fp1:';

/** Byte ranges fp1 hashes for a file of `size` bytes, as [offset, length] pairs. */
export declare function ranges(size: number | bigint): Array<[bigint, bigint]>;

/** Fingerprint from a size and a reader that must return exactly `length` bytes. */
export declare function fingerprintWith(
  size: number | bigint,
  readAt: (offset: bigint, length: number) => Uint8Array | Promise<Uint8Array>,
): Promise<string>;

/** Fingerprint of a Blob (browser File, Bun.file(), Node fs.openAsBlob()). */
export declare function fingerprintBlob(blob: Blob): Promise<string>;
