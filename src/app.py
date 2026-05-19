from __future__ import annotations

import argparse
import logging
import time
from dataclasses import dataclass

from .clip_library import ClipLibrary, ClipValidationError
from .config import ConfigError, load_config
from .dashboard import RuntimeStatus, create_dashboard_app
from .drop_detector import DropDetector
from .logging_setup import setup_logging
from .obs_client import OBSController, OBSStatus
from .scheduler import TriggerScheduler
from .state_machine import ShowState


@dataclass
class AgentRuntime:
    status: RuntimeStatus

    def pause(self) -> None:
        self.status.paused = True

    def resume(self) -> None:
        self.status.paused = False

    def hide_overlay(self) -> None:
        self.status.current_clip = None

    def test_random(self) -> None:
        self.status.last_trigger_reason = "test_random"

    def test_drop(self) -> None:
        self.status.last_trigger_reason = "test_drop"

    def blackout(self) -> None:
        self.status.blackout = True

    def clear_blackout(self) -> None:
        self.status.blackout = False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OBS Auto-Drop Visual Agent")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--manifest", default="clips_manifest.json")
    parser.add_argument("--mode", choices=["setup", "dry", "show"], default="dry")
    parser.add_argument("--once", action="store_true", help="Esegue solo i controlli iniziali e termina.")
    return parser


def load_runtime(args: argparse.Namespace) -> tuple[RuntimeStatus, AgentRuntime]:
    config = load_config(args.config)
    setup_logging(config.logging.level, config.logging.logs_dir)
    status = RuntimeStatus()
    status.setup_messages.append("Dashboard locale: OK su 127.0.0.1")
    if config.source_path and config.source_path.name == "config.example.yaml":
        status.setup_messages.append(
            "config.yaml manca: copia config.example.yaml in config.yaml o esegui setup.bat."
        )
    try:
        clips = ClipLibrary.from_manifest(args.manifest, validate_files=False)
        status.setup_messages.append(f"Manifest caricato: {len(clips.clips)} clip dichiarate.")
    except ClipValidationError as exc:
        status.setup_messages.append(f"Manifest da sistemare: {exc}")

    obs = OBSController(config)
    report = obs.diagnose_connection()
    status.obs_connected = report.status == OBSStatus.CONNECTED
    status.setup_messages.append(report.message)
    if report.detail:
        status.setup_messages.append(report.detail)

    detector = DropDetector(confidence_threshold=config.triggering.confidence_threshold)
    scheduler = TriggerScheduler(
        min_seconds_between_any_overlay=config.triggering.min_seconds_between_any_overlay,
        min_seconds_between_drop_overlays=config.triggering.min_seconds_between_drop_overlays,
        max_drop_overlays_per_hour=config.triggering.max_drop_overlays_per_hour,
    )
    del detector, scheduler
    runtime = AgentRuntime(status=status)
    if args.mode == "dry":
        status.state = ShowState.CALIBRATING
        status.last_trigger_reason = "dry_mode_no_obs_triggers"
    elif args.mode == "setup":
        status.state = ShowState.CALIBRATING
        status.last_trigger_reason = "setup_mode"
    else:
        status.state = ShowState.CALIBRATING
        status.last_trigger_reason = "show_mode"
    return status, runtime


def main() -> int:
    args = build_parser().parse_args()
    try:
        config = load_config(args.config)
        status, runtime = load_runtime(args)
    except ConfigError as exc:
        print(f"ERRORE: {exc}")
        print("Prossimo passo: fai doppio click su setup.bat.")
        return 2

    print("OBS Auto-Drop Agent")
    for message in status.setup_messages:
        print(f"- {message}")
    print(f"Dashboard: http://{config.network.dashboard_host}:{config.network.dashboard_port}")

    if args.once:
        return 0

    try:
        import uvicorn
    except ImportError:
        print("ERRORE: uvicorn non e' installato. Esegui setup.bat.")
        return 2

    app = create_dashboard_app(status, runtime)
    logging.getLogger(__name__).info("Dashboard avviato in modalita' %s", args.mode)
    try:
        uvicorn.run(
            app,
            host=config.network.dashboard_host,
            port=config.network.dashboard_port,
            log_level="info",
        )
    except KeyboardInterrupt:
        print("Chiusura richiesta dall'operatore.")
    finally:
        time.sleep(0.1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
