from __future__ import annotations

from dataclasses import dataclass

from .audio_features import AudioFeatures
from .state_machine import ShowState, StateMachine, StateSignals
from .utils import clamp01


@dataclass(frozen=True)
class DropScoreComponents:
    breakdown_strength: float
    build_slope: float
    onset_density_rise: float
    beat_phrase_alignment: float
    bass_return_probability: float

    def score(self) -> float:
        return clamp01(
            0.25 * self.breakdown_strength
            + 0.25 * self.build_slope
            + 0.20 * self.onset_density_rise
            + 0.15 * self.beat_phrase_alignment
            + 0.15 * self.bass_return_probability
        )


def score_drop_confidence(components: DropScoreComponents) -> float:
    return components.score()


@dataclass
class DropDetector:
    confidence_threshold: float = 0.78
    machine: StateMachine | None = None
    last_score: float = 0.0

    def __post_init__(self) -> None:
        if self.machine is None:
            self.machine = StateMachine(confidence_threshold=self.confidence_threshold)

    def score_from_features(self, features: AudioFeatures) -> DropScoreComponents:
        return DropScoreComponents(
            breakdown_strength=clamp01(1.0 - features.bass_presence),
            build_slope=clamp01((features.energy_slope + 1.0) / 2.0),
            onset_density_rise=clamp01(features.onset_score),
            beat_phrase_alignment=clamp01(features.beat_confidence),
            bass_return_probability=clamp01(features.bass_return_probability),
        )

    def update(self, features: AudioFeatures, *, calibration_done: bool = True) -> ShowState:
        components = self.score_from_features(features)
        self.last_score = components.score()
        signals = StateSignals(
            calibration_done=calibration_done,
            audio_healthy=features.signal_healthy,
            bass_suppressed=features.bass_presence < 0.55 and features.rms > 0.01,
            bass_returned=features.bass_presence > 1.15 and features.bass_return_probability > 0.6,
            energy_rising=features.energy_slope > 0.25,
            onset_density_rising=features.onset_score > 0.35,
            confidence=self.last_score,
        )
        assert self.machine is not None
        return self.machine.transition(signals)
