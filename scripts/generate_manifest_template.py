from __future__ import annotations

import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401


def build_manifest() -> dict[str, object]:
    clips = []
    for idx in range(1, 25):
        clips.append(
            {
                "id": f"drop_{idx:03d}",
                "file": f"clips/drop/drop_{idx:03d}.mp4",
                "category": "drop",
                "duration_ms": 12000,
                "impact_ms": 5200,
                "weight": 1.0,
                "min_seconds_between_repeats": 3600,
                "tags": ["astronaut", "drop"],
                "allowed_states": ["BUILD", "PEAK"],
                "max_plays_per_event": 2,
            }
        )
    for idx in range(1, 9):
        clips.append(
            {
                "id": f"random_{idx:03d}",
                "file": f"clips/random/random_{idx:03d}.mp4",
                "category": "random",
                "duration_ms": 10000,
                "impact_ms": None,
                "weight": 1.0,
                "min_seconds_between_repeats": 2400,
                "tags": ["astronaut", "ambient"],
                "allowed_states": ["NORMAL", "BREAKDOWN"],
                "max_plays_per_event": 2,
            }
        )
    for idx in range(1, 6):
        clips.append(
            {
                "id": f"peak_{idx:03d}",
                "file": f"clips/peak/peak_{idx:03d}.mp4",
                "category": "peak",
                "duration_ms": 11000,
                "impact_ms": 5200,
                "weight": 0.8,
                "min_seconds_between_repeats": 3600,
                "tags": ["astronaut", "peak"],
                "allowed_states": ["PEAK", "BUILD"],
                "max_plays_per_event": 1,
            }
        )
    for idx in range(1, 4):
        clips.append(
            {
                "id": f"calm_{idx:03d}",
                "file": f"clips/calm/calm_{idx:03d}.mp4",
                "category": "calm",
                "duration_ms": 10000,
                "impact_ms": None,
                "weight": 1.0,
                "min_seconds_between_repeats": 2400,
                "tags": ["astronaut", "calm"],
                "allowed_states": ["NORMAL", "BREAKDOWN"],
                "max_plays_per_event": 2,
            }
        )
    return {"clips": clips}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    text = json.dumps(build_manifest(), indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
        print(f"Manifest creato: {args.output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
