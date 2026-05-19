from __future__ import annotations

import os
import socket
import subprocess
from pathlib import Path
from typing import Iterable


LOCALHOST_VALUES = {"127.0.0.1", "localhost", "::1"}


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def is_localhost(host: str) -> bool:
    return (host or "").strip().lower() in LOCALHOST_VALUES


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def resolve_path(path: str | Path, base: Path | None = None) -> Path:
    raw = Path(path)
    if raw.is_absolute():
        return raw
    return ((base or project_root()) / raw).resolve()


def probe_tcp(host: str, port: int, timeout_sec: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout_sec):
            return True
    except OSError:
        return False


def obs_process_running() -> bool:
    if os.name != "nt":
        return False
    try:
        output = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq obs64.exe"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
    except Exception:
        return False
    return "obs64.exe" in output.lower()


def format_check(label: str, ok: bool, detail: str = "") -> str:
    prefix = "OK" if ok else "ERRORE"
    suffix = f" - {detail}" if detail else ""
    return f"{prefix}: {label}{suffix}"


def first_existing(paths: Iterable[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None
