from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .utils import is_localhost, project_root


class ConfigError(RuntimeError):
    """Raised for beginner-facing configuration errors."""


@dataclass(frozen=True)
class ObsConfig:
    host: str = "127.0.0.1"
    port: int = 4455
    password_env: str = "OBS_WS_PASSWORD"
    scene_name: str = "SHOW_MAIN"
    background_source_name: str = "BG_SYNES_SPOUT"
    overlay_source_name: str = "OVERLAY_VIDEO"
    flash_source_name: str = "FLASH_WHITE"
    blackout_source_name: str = "BLACKOUT"
    chroma_filter_name: str = "KEY_GREEN"


@dataclass(frozen=True)
class NetworkConfig:
    local_only: bool = True
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 8787
    allow_lan: bool = False


@dataclass(frozen=True)
class AudioConfig:
    input_device_name: str | None = None
    sample_rate: int = 48000
    block_size: int = 1024
    channels: int = 1
    calibration_seconds: int = 180


@dataclass(frozen=True)
class TriggeringConfig:
    mode: str = "auto_only"
    enable_random_ambient: bool = True
    enable_drop_preroll: bool = True
    min_seconds_between_any_overlay: int = 240
    min_seconds_between_drop_overlays: int = 420
    max_drop_overlays_per_hour: int = 6
    confidence_threshold: float = 0.78
    preroll_tolerance_ms: int = 500
    default_impact_ms: int = 5200
    random_interval_min_sec: int = 420
    random_interval_max_sec: int = 900
    skip_if_audio_confidence_low: bool = True


@dataclass(frozen=True)
class VisualsConfig:
    flash_enabled: bool = True
    flash_duration_ms: int = 150
    overlay_fade_in_ms: int = 100
    overlay_fade_out_ms: int = 250
    hide_overlay_after_clip: bool = True


@dataclass(frozen=True)
class SafetyConfig:
    auto_hide_on_obs_error: bool = True
    auto_hide_on_audio_silence_sec: int = 5
    blackout_hotkey: str = "b"
    pause_hotkey: str = "space"
    test_drop_hotkey: str = "d"
    test_random_hotkey: str = "r"


@dataclass(frozen=True)
class LoggingConfig:
    level: str = "INFO"
    write_jsonl: bool = True
    write_csv_features: bool = True
    logs_dir: str = "logs"


@dataclass(frozen=True)
class AppConfig:
    obs: ObsConfig = field(default_factory=ObsConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    triggering: TriggeringConfig = field(default_factory=TriggeringConfig)
    visuals: VisualsConfig = field(default_factory=VisualsConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    source_path: Path | None = None

    def validate_local_only(self) -> None:
        if self.network.local_only and not self.network.allow_lan:
            if not is_localhost(self.network.dashboard_host):
                raise ConfigError(
                    "Il dashboard deve ascoltare solo su 127.0.0.1. "
                    "Correggi network.dashboard_host in config.yaml."
                )
            if not is_localhost(self.obs.host):
                raise ConfigError(
                    "OBS deve essere controllato solo su 127.0.0.1. "
                    "Correggi obs.host in config.yaml."
                )

    def obs_password(self) -> str:
        return os.environ.get(self.obs.password_env, "")


def _section(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError(f"La sezione '{key}' in config.yaml non e' valida.")
    return value


def _make(cls: type[Any], values: dict[str, Any]) -> Any:
    allowed = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
    unknown = sorted(set(values) - allowed)
    if unknown:
        raise ConfigError(f"Chiavi non riconosciute in {cls.__name__}: {', '.join(unknown)}")
    return cls(**values)


def app_config_from_mapping(data: dict[str, Any], source_path: Path | None = None) -> AppConfig:
    cfg = AppConfig(
        obs=_make(ObsConfig, _section(data, "obs")),
        network=_make(NetworkConfig, _section(data, "network")),
        audio=_make(AudioConfig, _section(data, "audio")),
        triggering=_make(TriggeringConfig, _section(data, "triggering")),
        visuals=_make(VisualsConfig, _section(data, "visuals")),
        safety=_make(SafetyConfig, _section(data, "safety")),
        logging=_make(LoggingConfig, _section(data, "logging")),
        source_path=source_path,
    )
    cfg.validate_local_only()
    return cfg


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise ConfigError(
            "PyYAML non e' installato. Esegui setup.bat prima di usare l'app."
        ) from exc
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ConfigError("config.yaml deve contenere un oggetto YAML.")
    return data


def load_env_file(path: str | Path = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_config(path: str | Path = "config.yaml", *, allow_example_fallback: bool = True) -> AppConfig:
    load_env_file(project_root() / ".env")
    requested = Path(path)
    if not requested.is_absolute():
        requested = project_root() / requested
    if requested.exists():
        return app_config_from_mapping(load_yaml(requested), requested)
    example = project_root() / "config.example.yaml"
    if allow_example_fallback and example.exists():
        return app_config_from_mapping(load_yaml(example), example)
    raise ConfigError(
        "config.yaml non trovato. Esegui setup.bat oppure copia config.example.yaml in config.yaml."
    )


def copy_default_files(root: Path | None = None) -> list[Path]:
    base = root or project_root()
    copied: list[Path] = []
    pairs = [
        (base / ".env.example", base / ".env"),
        (base / "config.example.yaml", base / "config.yaml"),
        (base / "clips_manifest.example.json", base / "clips_manifest.json"),
    ]
    for source, target in pairs:
        if source.exists() and not target.exists():
            shutil.copyfile(source, target)
            copied.append(target)
    return copied
