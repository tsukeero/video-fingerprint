use std::io;
use video_fingerprint::{fingerprint_file, fingerprint_with, ranges, CHUNK};

/// Test content per SPEC.md: 64 KiB blocks, block i = BLAKE3 XOF(name || u64le(i))[..65536].
fn content_reader(name: &str) -> impl FnMut(u64, &mut [u8]) -> io::Result<()> {
    let prefix = name.as_bytes().to_vec();
    let mut block = vec![0u8; CHUNK as usize];
    move |off, buf| {
        let mut done = 0usize;
        while done < buf.len() {
            let pos = off + done as u64;
            let (i, r) = (pos / CHUNK, (pos % CHUNK) as usize);
            let mut h = blake3::Hasher::new();
            h.update(&prefix);
            h.update(&i.to_le_bytes());
            h.finalize_xof().fill(&mut block);
            let n = (CHUNK as usize - r).min(buf.len() - done);
            buf[done..done + n].copy_from_slice(&block[r..r + n]);
            done += n;
        }
        Ok(())
    }
}

fn vectors() -> Vec<(String, u64, String)> {
    let text = std::fs::read_to_string(concat!(env!("CARGO_MANIFEST_DIR"), "/../vectors/vectors.json")).unwrap();
    let v: serde_json::Value = serde_json::from_str(&text).unwrap();
    v["vectors"]
        .as_array()
        .unwrap()
        .iter()
        .map(|x| {
            (
                x["name"].as_str().unwrap().to_string(),
                x["size"].as_str().unwrap().parse().unwrap(),
                x["fingerprint"].as_str().unwrap().to_string(),
            )
        })
        .collect()
}

#[test]
fn all_vectors_match() {
    let vs = vectors();
    assert!(vs.len() >= 10);
    for (name, size, want) in vs {
        let got = fingerprint_with(size, content_reader(&name)).unwrap();
        assert_eq!(got, want, "vector {name} (size {size})");
    }
}

#[test]
fn file_matches_callback() {
    // Real file path through fingerprint_file, for a size that uses all three chunks.
    let name = "file-roundtrip";
    let size = 5 * CHUNK + 123;
    let mut data = vec![0u8; size as usize];
    content_reader(name)(0, &mut data).unwrap();
    let path = std::env::temp_dir().join(format!("vfp-test-{}.bin", std::process::id()));
    std::fs::write(&path, &data).unwrap();
    let a = fingerprint_file(&path).unwrap();
    std::fs::remove_file(&path).unwrap();
    let b = fingerprint_with(size, content_reader(name)).unwrap();
    assert_eq!(a, b);
}

#[test]
fn short_read_is_error() {
    let r = fingerprint_with(10 * CHUNK, |off, _buf| {
        if off > 0 { Err(io::Error::from(io::ErrorKind::UnexpectedEof)) } else { Ok(()) }
    });
    assert!(r.is_err());
}

#[test]
fn ranges_disjoint_above_threshold() {
    for size in [3 * CHUNK + 1, 3 * CHUNK + 2, 4 * CHUNK, 7 * CHUNK + 5, u64::MAX] {
        let r = ranges(size);
        assert_eq!(r.len(), 3);
        assert!(r[0].0 + r[0].1 <= r[1].0, "size {size}");
        assert!(r[1].0 + r[1].1 <= r[2].0, "size {size}");
        assert_eq!(r[2].0 + r[2].1, size);
    }
    assert_eq!(ranges(3 * CHUNK), vec![(0, 3 * CHUNK)]);
    assert_eq!(ranges(0), vec![(0, 0)]);
}

#[test]
fn format() {
    let fp = fingerprint_with(0, |_, _| Ok(())).unwrap();
    assert_eq!(fp.len(), 36);
    assert!(fp.starts_with("fp1:"));
    assert!(fp[4..].chars().all(|c| matches!(c, '0'..='9' | 'a'..='f')));
}
