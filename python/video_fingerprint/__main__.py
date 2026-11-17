"""python -m video_fingerprint FILE...  prints `<fingerprint>  <path>` per file."""
import sys

from . import fingerprint_file


def main() -> int:
    failed = False
    for p in sys.argv[1:]:
        try:
            print(f"{fingerprint_file(p)}  {p}")
        except (OSError, EOFError) as e:
            print(f"{p}: {e}", file=sys.stderr)
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
