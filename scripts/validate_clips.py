from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401

from src.clip_library import ClipLibrary, ClipValidationError


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="clips_manifest.json")
    parser.add_argument("--strict-files", action="store_true")
    args = parser.parse_args()
    try:
        library = ClipLibrary.from_manifest(args.manifest, validate_files=False)
        print("OK: manifest valido")
        print("Conteggio per categoria:")
        for category, count in library.summary().items():
            print(f"- {category}: {count}")
        missing = [clip.file for clip in library.clips if not clip.absolute_path(library.root).exists()]
        if missing:
            print("\nATTENZIONE: questi file video non esistono ancora:")
            for item in missing:
                print(f"- {item}")
            if args.strict_files:
                return 1
            print("Per ora va bene se stai usando il manifest esempio.")
        return 0
    except ClipValidationError as exc:
        print(f"ERRORE: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
