from __future__ import annotations

from src.drop_detector import DropScoreComponents, score_drop_confidence


def test_score_is_weighted_sum():
    score = score_drop_confidence(
        DropScoreComponents(
            breakdown_strength=1.0,
            build_slope=1.0,
            onset_density_rise=1.0,
            beat_phrase_alignment=1.0,
            bass_return_probability=1.0,
        )
    )
    assert score == 1.0


def test_score_is_clamped():
    score = score_drop_confidence(
        DropScoreComponents(
            breakdown_strength=10.0,
            build_slope=10.0,
            onset_density_rise=10.0,
            beat_phrase_alignment=10.0,
            bass_return_probability=10.0,
        )
    )
    assert score == 1.0


def test_low_signal_has_low_score():
    score = score_drop_confidence(
        DropScoreComponents(
            breakdown_strength=0.1,
            build_slope=0.1,
            onset_density_rise=0.1,
            beat_phrase_alignment=0.0,
            bass_return_probability=0.0,
        )
    )
    assert 0.0 <= score < 0.1
