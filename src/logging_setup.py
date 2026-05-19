from __future__ import annotations

import logging
from pathlib import Path


def setup_logging(level: str = "INFO", logs_dir: str = "logs") -> None:
    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(Path(logs_dir) / "agent.log", encoding="utf-8"),
        ],
    )
