from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ShowState(str, Enum):
    CALIBRATING = "CALIBRATING"
    NORMAL = "NORMAL"
    BREAKDOWN_CANDIDATE = "BREAKDOWN_CANDIDATE"
    BREAKDOWN = "BREAKDOWN"
    BUILD = "BUILD"
    PREROLL_ARMED = "PREROLL_ARMED"
    PREROLL_PLAYING = "PREROLL_PLAYING"
    IMPACT = "IMPACT"
    COOLDOWN = "COOLDOWN"
    PAUSED = "PAUSED"
    ERROR = "ERROR"


@dataclass(frozen=True)
class StateSignals:
    calibration_done: bool = False
    audio_healthy: bool = True
    bass_suppressed: bool = False
    bass_returned: bool = False
    energy_rising: bool = False
    onset_density_rising: bool = False
    confidence: float = 0.0
    cooldown_done: bool = False
    overlay_finished: bool = False
    pause_requested: bool = False
    resume_requested: bool = False
    error: bool = False


@dataclass
class StateMachine:
    state: ShowState = ShowState.CALIBRATING
    confidence_threshold: float = 0.78

    def transition(self, signals: StateSignals) -> ShowState:
        if signals.error:
            self.state = ShowState.ERROR
            return self.state
        if signals.pause_requested:
            self.state = ShowState.PAUSED
            return self.state
        if self.state == ShowState.PAUSED:
            if signals.resume_requested:
                self.state = ShowState.NORMAL
            return self.state
        if not signals.audio_healthy:
            self.state = ShowState.ERROR
            return self.state
        if self.state == ShowState.CALIBRATING:
            if signals.calibration_done:
                self.state = ShowState.NORMAL
        elif self.state == ShowState.NORMAL:
            if signals.bass_suppressed:
                self.state = ShowState.BREAKDOWN_CANDIDATE
        elif self.state == ShowState.BREAKDOWN_CANDIDATE:
            if not signals.bass_suppressed:
                self.state = ShowState.NORMAL
            elif signals.energy_rising or signals.onset_density_rising:
                self.state = ShowState.BREAKDOWN
        elif self.state == ShowState.BREAKDOWN:
            if signals.energy_rising and signals.onset_density_rising:
                self.state = ShowState.BUILD
        elif self.state == ShowState.BUILD:
            if signals.confidence >= self.confidence_threshold:
                self.state = ShowState.PREROLL_ARMED
            elif signals.bass_returned:
                self.state = ShowState.NORMAL
        elif self.state == ShowState.PREROLL_ARMED:
            self.state = ShowState.PREROLL_PLAYING
        elif self.state == ShowState.PREROLL_PLAYING:
            if signals.bass_returned:
                self.state = ShowState.IMPACT
            elif signals.overlay_finished:
                self.state = ShowState.COOLDOWN
        elif self.state == ShowState.IMPACT:
            if signals.overlay_finished:
                self.state = ShowState.COOLDOWN
        elif self.state == ShowState.COOLDOWN:
            if signals.cooldown_done:
                self.state = ShowState.NORMAL
        elif self.state == ShowState.ERROR:
            if signals.resume_requested and signals.audio_healthy:
                self.state = ShowState.NORMAL
        return self.state
