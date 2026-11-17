//! fp1 quick fingerprint for large video files. See `../SPEC.md`.

use std::fs::File;
use std::io::{self, Read, Seek, SeekFrom};
use std::path::Path;

pub const CHUNK: u64 = 65536;
pub const CONTEXT: &str = "video-fingerprint 2026-11-17 fp1";
pub const PREFIX: &str = "fp1:";

/// The byte ranges fp1 hashes for a file of `size` bytes, in hashing order.
pub fn ranges(size: u64) -> Vec<(u64, u64)> {
    if size <= 3 * CHUNK {
        return vec![(0, size)];
    }
    let mid = (size - CHUNK) / 2;
    vec![(0, CHUNK), (mid, CHUNK), (size - CHUNK, CHUNK)]
}

/// Fingerprint from a size and a reader callback `read_at(offset, buf)` that must fill `buf`
/// completely or return an error.
pub fn fingerprint_with<F>(size: u64, mut read_at: F) -> io::Result<String>
where
    F: FnMut(u64, &mut [u8]) -> io::Result<()>,
{
    let mut h = blake3::Hasher::new_derive_key(CONTEXT);
    h.update(&size.to_le_bytes());
    let mut buf = vec![0u8; CHUNK as usize];
    for (off, len) in ranges(size) {
        // Whole-file case is at most 3 * CHUNK; read it in CHUNK pieces.
        let mut done = 0;
        while done < len {
            let n = (len - done).min(CHUNK) as usize;
            read_at(off + done, &mut buf[..n])?;
            h.update(&buf[..n]);
            done += n as u64;
        }
    }
    let out = h.finalize();
    let mut s = String::with_capacity(PREFIX.len() + 32);
    s.push_str(PREFIX);
    for b in &out.as_bytes()[..16] {
        s.push_str(&format!("{b:02x}"));
    }
    Ok(s)
}

/// Fingerprint of any seekable reader whose length is `size`.
pub fn fingerprint_reader<R: Read + Seek>(r: &mut R, size: u64) -> io::Result<String> {
    fingerprint_with(size, |off, buf| {
        r.seek(SeekFrom::Start(off))?;
        r.read_exact(buf)
    })
}

/// Fingerprint of a file on disk. The size is taken once, at open time.
pub fn fingerprint_file(path: impl AsRef<Path>) -> io::Result<String> {
    let mut f = File::open(path)?;
    let size = f.metadata()?.len();
    fingerprint_reader(&mut f, size)
}
