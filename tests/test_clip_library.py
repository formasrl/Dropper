from __future__ import annotations

import json
import random

import pytest

from src.clip_library import ClipLibrary, ClipValidationError


def write_manifest(tmp_path, clips):
    path = tmp_path / "clips_manifest.json"
    path.write_text(json.dumps({"clips": clips}), encoding="utf-8")
    return path


def base_clip(**overrides):
    data = {
        "id": "drop_001",
        "file": "clips/drop/drop_001.mp4",
        "category": "drop",
        "duration_ms": 12000,
        "impact_ms": 5200,
        "weight": 1.0,
        "min_seconds_between_repeats": 3600,
        "tags": ["drop"],
        "allowed_states": ["BUILD"],
        "max_plays_per_event": 2,
    }
    data.update(overrides)
    return data


def test_manifest_loads_and_summarizes(tmp_path):
    manifest = write_manifest(
        tmp_path,
        [
            base_clip(),
            base_clip(id="random_001", category="random", impact_ms=None, allowed_states=["NORMAL"]),
        ],
    )
    library = ClipLibrary.from_manifest(manifest)
    assert len(library.clips) == 2
    assert library.summary()["drop"] == 1
    assert library.summary()["random"] == 1


def test_validate_files_reports_missing_relative_to_manifest(tmp_path):
    manifest = write_manifest(tmp_path, [base_clip()])
    library = ClipLibrary.from_manifest(manifest)
    with pytest.raises(ClipValidationError) as error:
        library.validate_files()
    assert "clips/drop/drop_001.mp4" in str(error.value)


def test_duplicate_ids_are_rejected(tmp_path):
    manifest = write_manifest(tmp_path, [base_clip(), base_clip()])
    with pytest.raises(ClipValidationError):
        ClipLibrary.from_manifest(manifest)


def test_choose_clip_respects_state_and_repeat_cooldown(tmp_path):
    manifest = write_manifest(tmp_path, [base_clip()])
    library = ClipLibrary.from_manifest(manifest)
    rng = random.Random(7)
    selected = library.choose_clip("drop", state="NORMAL", now=0, rng=rng)
    assert selected is None
    selected = library.choose_clip("drop", state="BUILD", now=0, rng=rng)
    assert selected is not None
    library.record_play(selected.id, now=0)
    assert library.choose_clip("drop", state="BUILD", now=120, rng=rng) is None
    assert library.choose_clip("drop", state="BUILD", now=3700, rng=rng) is not None
