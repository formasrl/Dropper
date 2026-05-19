from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .utils import project_root, resolve_path


class ClipValidationError(RuntimeError):
    """Raised when the clip manifest is malformed or unusable."""


VALID_CATEGORIES = {"drop", "random", "peak", "calm", "test"}


@dataclass(frozen=True)
class Clip:
    id: str
    file: str
    category: str
    duration_ms: int
    impact_ms: int | None
    weight: float = 1.0
    min_seconds_between_repeats: int = 3600
    tags: tuple[str, ...] = ()
    allowed_states: tuple[str, ...] = ()
    max_plays_per_event: int = 2

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Clip":
        required = ["id", "file", "category", "duration_ms"]
        missing = [key for key in required if key not in raw]
        if missing:
            raise ClipValidationError(f"Clip senza campi obbligatori: {', '.join(missing)}")
        category = str(raw["category"])
        if category not in VALID_CATEGORIES:
            raise ClipValidationError(f"Categoria clip non valida: {category}")
        duration_ms = int(raw["duration_ms"])
        if duration_ms <= 0:
            raise ClipValidationError(f"duration_ms non valido per {raw['id']}")
        impact_raw = raw.get("impact_ms")
        impact_ms = None if impact_raw is None else int(impact_raw)
        if impact_ms is not None and not (0 <= impact_ms <= duration_ms):
            raise ClipValidationError(f"impact_ms fuori range per {raw['id']}")
        weight = float(raw.get("weight", 1.0))
        if weight <= 0:
            raise ClipValidationError(f"weight deve essere positivo per {raw['id']}")
        return cls(
            id=str(raw["id"]),
            file=str(raw["file"]),
            category=category,
            duration_ms=duration_ms,
            impact_ms=impact_ms,
            weight=weight,
            min_seconds_between_repeats=int(raw.get("min_seconds_between_repeats", 3600)),
            tags=tuple(str(item) for item in raw.get("tags", [])),
            allowed_states=tuple(str(item) for item in raw.get("allowed_states", [])),
            max_plays_per_event=int(raw.get("max_plays_per_event", 2)),
        )

    def absolute_path(self, base: Path | None = None) -> Path:
        return resolve_path(self.file, base or project_root())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "file": self.file,
            "category": self.category,
            "duration_ms": self.duration_ms,
            "impact_ms": self.impact_ms,
            "weight": self.weight,
            "min_seconds_between_repeats": self.min_seconds_between_repeats,
            "tags": list(self.tags),
            "allowed_states": list(self.allowed_states),
            "max_plays_per_event": self.max_plays_per_event,
        }


@dataclass
class ClipLibrary:
    clips: list[Clip]
    root: Path = field(default_factory=project_root)
    play_history: dict[str, list[float]] = field(default_factory=dict)

    @classmethod
    def from_manifest(cls, path: str | Path, *, validate_files: bool = False) -> "ClipLibrary":
        manifest_path = Path(path)
        if not manifest_path.is_absolute():
            manifest_path = project_root() / manifest_path
        if not manifest_path.exists():
            example = project_root() / "clips_manifest.example.json"
            if example.exists():
                manifest_path = example
            else:
                raise ClipValidationError(
                    "clips_manifest.json non trovato. Esegui setup.bat o genera un manifest."
                )
        with manifest_path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        if not isinstance(raw, dict) or not isinstance(raw.get("clips"), list):
            raise ClipValidationError("Il manifest deve contenere una lista 'clips'.")
        clips = [Clip.from_dict(item) for item in raw["clips"]]
        ids = [clip.id for clip in clips]
        duplicates = sorted({clip_id for clip_id in ids if ids.count(clip_id) > 1})
        if duplicates:
            raise ClipValidationError(f"ID clip duplicati: {', '.join(duplicates)}")
        lib = cls(clips=clips, root=manifest_path.parent)
        if validate_files:
            lib.validate_files()
        return lib

    def validate_files(self) -> list[str]:
        missing = [clip.file for clip in self.clips if not clip.absolute_path(self.root).exists()]
        if missing:
            raise ClipValidationError("Clip mancanti:\n" + "\n".join(missing))
        return []

    def by_category(self, categories: str | Iterable[str]) -> list[Clip]:
        wanted = {categories} if isinstance(categories, str) else set(categories)
        return [clip for clip in self.clips if clip.category in wanted]

    def is_allowed_now(self, clip: Clip, *, state: str, now: float) -> bool:
        if clip.allowed_states and state not in clip.allowed_states:
            return False
        history = self.play_history.get(clip.id, [])
        if len(history) >= clip.max_plays_per_event:
            return False
        if history and now - max(history) < clip.min_seconds_between_repeats:
            return False
        return True

    def choose_clip(
        self,
        categories: str | Iterable[str],
        *,
        state: str,
        now: float,
        rng: random.Random | None = None,
    ) -> Clip | None:
        candidates = [
            clip
            for clip in self.by_category(categories)
            if self.is_allowed_now(clip, state=state, now=now)
        ]
        if not candidates:
            return None
        chooser = rng or random
        weights = [clip.weight for clip in candidates]
        return chooser.choices(candidates, weights=weights, k=1)[0]

    def record_play(self, clip_id: str, now: float) -> None:
        self.play_history.setdefault(clip_id, []).append(float(now))

    def summary(self) -> dict[str, int]:
        result: dict[str, int] = {category: 0 for category in sorted(VALID_CATEGORIES)}
        for clip in self.clips:
            result[clip.category] += 1
        return result
