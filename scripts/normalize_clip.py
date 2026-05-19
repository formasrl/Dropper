from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401

from src.video_tools import VideoToolError, normalize_video, probe_video


def default_output(input_path: Path, category: str | None) -> Path:
    category_dir = category or "test"
    return Path("clips") / category_dir / f"{input_path.stem}_normalized.mp4"


def print_probe(path: Path) -> None:
    probe = probe_video(path)
    print(f"File: {probe.path}")
    print(f"Durata: {probe.duration_ms} ms")
    print(f"Formato: {probe.width}x{probe.height}, {probe.fps:.2f} fps, codec {probe.video_codec}")
    print(f"Audio: {'presente' if probe.audio_streams else 'assente'}")
    if probe.is_target_format:
        print("OK: clip gia' compatibile con il formato consigliato.")
    else:
        print("ATTENZIONE: da normalizzare:")
        for note in probe.compatibility_notes():
            print(f"- {note}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida o converte una clip per OBS Auto-Drop.")
    parser.add_argument("input", help="File video da controllare o convertire")
    parser.add_argument("--output", default=None, help="Percorso MP4 normalizzato")
    parser.add_argument("--category", choices=["drop", "random", "peak", "calm", "test"], default="test")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    source = Path(args.input)
    try:
        print_probe(source)
        if args.check_only:
            return 0
        output = Path(args.output) if args.output else default_output(source, args.category)
        print(f"\nConverto in: {output}")
        normalized = normalize_video(source, output, overwrite=args.overwrite)
        print("OK: conversione completata.")
        print_probe(normalized)
        return 0
    except VideoToolError as exc:
        print(f"ERRORE: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
