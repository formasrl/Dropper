from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass
class BasicBeatTracker:
    """Small fallback beat tracker based on onset timestamps."""

    onset_times: deque[float] = field(default_factory=lambda: deque(maxlen=32))
    bpm_estimate: float | None = None
    beat_confidence: float = 0.0

    def add_onset(self, timestamp: float) -> tuple[float | None, float]:
        self.onset_times.append(float(timestamp))
        if len(self.onset_times) < 4:
            self.bpm_estimate = None
            self.beat_confidence = 0.0
            return self.bpm_estimate, self.beat_confidence
        intervals = [
            b - a
            for a, b in zip(list(self.onset_times), list(self.onset_times)[1:])
            if 0.25 <= b - a <= 1.2
        ]
        if not intervals:
            self.bpm_estimate = None
            self.beat_confidence = 0.0
            return self.bpm_estimate, self.beat_confidence
        avg = sum(intervals) / len(intervals)
        variance = sum((item - avg) ** 2 for item in intervals) / len(intervals)
        self.bpm_estimate = 60.0 / avg
        self.beat_confidence = max(0.0, min(1.0, 1.0 - variance * 8.0))
        return self.bpm_estimate, self.beat_confidence
