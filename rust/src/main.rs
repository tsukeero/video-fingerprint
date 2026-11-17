//! `vfp FILE...` prints `<fingerprint>  <path>` per file (errors go to stderr, exit code 1).

fn main() {
    let mut failed = false;
    for p in std::env::args_os().skip(1) {
        match video_fingerprint::fingerprint_file(&p) {
            Ok(fp) => println!("{fp}  {}", p.to_string_lossy()),
            Err(e) => {
                eprintln!("{}: {e}", p.to_string_lossy());
                failed = true;
            }
        }
    }
    std::process::exit(failed as i32);
}
