from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class VideoToolError(RuntimeError):
    pass


@dataclass(frozen=True)
class VideoProbe:
    path: Path
    duration_ms: int
    width: int
    height: int
    fps: float
    video_codec: str
    audio_streams: int
    pixel_format: str | None = None

    @property
    def is_target_format(self) -> bool:
        return (
            self.path.suffix.lower() == ".mp4"
            and self.video_codec in {"h264", "avc1"}
            and self.width == 1920
            and self.height == 1080
            and self.fps >= 59.0
            and self.audio_streams == 0
        )

    def compatibility_notes(self) -> list[str]:
        notes: list[str] = []
        if self.path.suffix.lower() != ".mp4":
            notes.append("Il file non e' MP4.")
        if self.video_codec not in {"h264", "avc1"}:
            notes.append(f"Codec video non ideale: {self.video_codec}. Serve H.264.")
        if (self.width, self.height) != (1920, 1080):
            notes.append(f"Risoluzione {self.width}x{self.height}. Serve 1920x1080.")
        if self.fps < 59.0:
            notes.append(f"FPS circa {self.fps:.2f}. Consigliato 60 fps.")
        if self.audio_streams:
            notes.append("Il file contiene audio. Consigliato nessun audio.")
        return notes

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "duration_ms": self.duration_ms,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "video_codec": self.video_codec,
            "audio_streams": self.audio_streams,
            "pixel_format": self.pixel_format,
            "is_target_format": self.is_target_format,
            "notes": self.compatibility_notes(),
        }


def require_tool(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise VideoToolError(
            f"{name} non trovato. Installa FFmpeg durante il setup e poi rilancia il tool."
        )
    return found


def _parse_rate(value: str | None) -> float:
    if not value or value == "0/0":
        return 0.0
    if "/" in value:
        left, right = value.split("/", 1)
        denominator = float(right)
        return 0.0 if denominator == 0 else float(left) / denominator
    return float(value)


def probe_video(path: str | Path) -> VideoProbe:
    ffprobe = require_tool("ffprobe")
    video_path = Path(path).resolve()
    if not video_path.exists():
        raise VideoToolError(f"File non trovato: {video_path}")
    command = [
        ffprobe,
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(video_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise VideoToolError(result.stderr.strip() or "ffprobe non riesce a leggere il file.")
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    video_stream = next((item for item in streams if item.get("codec_type") == "video"), None)
    if not video_stream:
        raise VideoToolError("Il file non contiene uno stream video.")
    duration = video_stream.get("duration") or data.get("format", {}).get("duration") or 0
    return VideoProbe(
        path=video_path,
        duration_ms=int(round(float(duration) * 1000)),
        width=int(video_stream.get("width", 0)),
        height=int(video_stream.get("height", 0)),
        fps=_parse_rate(video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate")),
        video_codec=str(video_stream.get("codec_name", "")),
        audio_streams=sum(1 for item in streams if item.get("codec_type") == "audio"),
        pixel_format=video_stream.get("pix_fmt"),
    )


def normalize_video(
    input_path: str | Path,
    output_path: str | Path,
    *,
    fps: int = 60,
    width: int = 1920,
    height: int = 1080,
    crf: int = 18,
    overwrite: bool = False,
) -> Path:
    ffmpeg = require_tool("ffmpeg")
    source = Path(input_path).resolve()
    target = Path(output_path).resolve()
    if not source.exists():
        raise VideoToolError(f"File non trovato: {source}")
    if target.exists() and not overwrite:
        raise VideoToolError(f"Output gia' esistente: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    scale_filter = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x00ff00,"
        "format=yuv420p"
    )
    command = [
        ffmpeg,
        "-y" if overwrite else "-n",
        "-i",
        str(source),
        "-an",
        "-vf",
        scale_filter,
        "-r",
        str(fps),
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        str(crf),
        "-movflags",
        "+faststart",
        str(target),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise VideoToolError(result.stderr.strip() or "ffmpeg non e' riuscito a convertire il file.")
    return target


def transform_video(
    input_path: str | Path,
    output_path: str | Path,
    *,
    hflip: bool = False,
    vflip: bool = False,
    reverse: bool = False,
    fps: int = 60,
    width: int = 1920,
    height: int = 1080,
    crf: int = 18,
    overwrite: bool = False,
) -> Path:
    ffmpeg = require_tool("ffmpeg")
    source = Path(input_path).resolve()
    target = Path(output_path).resolve()
    if not source.exists():
        raise VideoToolError(f"File non trovato: {source}")
    if target.exists() and not overwrite:
        raise VideoToolError(f"Output gia' esistente: {target}")
    if not any([hflip, vflip, reverse]):
        raise VideoToolError("Scegli almeno una trasformazione: flip orizzontale, verticale o reverse.")
    target.parent.mkdir(parents=True, exist_ok=True)
    filters: list[str] = []
    if hflip:
        filters.append("hflip")
    if vflip:
        filters.append("vflip")
    if reverse:
        filters.append("reverse")
    filters.extend(
        [
            f"scale={width}:{height}:force_original_aspect_ratio=decrease",
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x00ff00",
            "format=yuv420p",
        ]
    )
    command = [
        ffmpeg,
        "-y" if overwrite else "-n",
        "-i",
        str(source),
        "-an",
        "-vf",
        ",".join(filters),
        "-r",
        str(fps),
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        str(crf),
        "-movflags",
        "+faststart",
        str(target),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise VideoToolError(result.stderr.strip() or "ffmpeg non e' riuscito a trasformare il file.")
    return target
