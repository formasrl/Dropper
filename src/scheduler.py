from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TriggerDecision:
    allowed: bool
    reason: str
    cooldown_remaining_sec: float = 0.0


@dataclass
class TriggerScheduler:
    min_seconds_between_any_overlay: int = 240
    min_seconds_between_drop_overlays: int = 420
    max_drop_overlays_per_hour: int = 6
    overlay_history: deque[tuple[float, str]] = field(default_factory=deque)

    def _prune(self, now: float) -> None:
        while self.overlay_history and now - self.overlay_history[0][0] > 3600:
            self.overlay_history.popleft()

    def can_trigger(self, category: str, now: float) -> TriggerDecision:
        self._prune(now)
        if self.overlay_history:
            elapsed = now - self.overlay_history[-1][0]
            if elapsed < self.min_seconds_between_any_overlay:
                return TriggerDecision(
                    False,
                    "cooldown_any_overlay",
                    self.min_seconds_between_any_overlay - elapsed,
                )
        if category == "drop":
            drop_times = [ts for ts, kind in self.overlay_history if kind == "drop"]
            if drop_times:
                elapsed_drop = now - drop_times[-1]
                if elapsed_drop < self.min_seconds_between_drop_overlays:
                    return TriggerDecision(
                        False,
                        "cooldown_drop_overlay",
                        self.min_seconds_between_drop_overlays - elapsed_drop,
                    )
            if len(drop_times) >= self.max_drop_overlays_per_hour:
                return TriggerDecision(False, "max_drop_overlays_per_hour")
        return TriggerDecision(True, "allowed")

    def record_trigger(self, category: str, now: float) -> None:
        self._prune(now)
        self.overlay_history.append((float(now), category))

    def cooldown_remaining(self, now: float) -> float:
        if not self.overlay_history:
            return 0.0
        return max(0.0, self.min_seconds_between_any_overlay - (now - self.overlay_history[-1][0]))
