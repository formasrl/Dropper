from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401

from src.audio_capture import list_audio_devices
from src.clip_library import ClipLibrary, ClipValidationError
from src.config import ConfigError, load_config
from src.obs_client import OBSController, OBSStatus


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--manifest", default="clips_manifest.json")
    args = parser.parse_args()

    ok = True
    try:
        config = load_config(args.config)
        print("OK: config caricata")
        print("OK: runtime locale su 127.0.0.1")
    except ConfigError as exc:
        print(f"ERRORE: config non valida - {exc}")
        return 1

    report = OBSController(config).diagnose_connection()
    print(report.message)
    if report.detail:
        print(report.detail)
    if report.status != OBSStatus.CONNECTED:
        ok = False

    devices = list_audio_devices()
    if devices:
        print(f"OK: ingressi audio trovati - {len(devices)}")
        if config.audio.input_device_name:
            print(f"Audio configurato: {config.audio.input_device_name}")
        else:
            print("ATTENZIONE: audio.input_device_name non scelto. Il wizard chiedera' quale usare.")
    else:
        print("ERRORE: nessun ingresso audio trovato o sounddevice non installato.")
        ok = False

    try:
        library = ClipLibrary.from_manifest(args.manifest, validate_files=False)
        print(f"OK: manifest clip leggibile - {len(library.clips)} clip")
        missing = [clip.file for clip in library.clips if not clip.absolute_path(library.root).exists()]
        if missing:
            print("ATTENZIONE: clip mancanti:")
            for item in missing[:20]:
                print(f"- {item}")
            if len(missing) > 20:
                print(f"... altre {len(missing) - 20}")
            print("Prima dello show questi file devono esistere.")
    except ClipValidationError as exc:
        print(f"ERRORE: manifest clip non valido - {exc}")
        ok = False

    if ok:
        print("\nRISULTATO: controlli base OK.")
        return 0
    print("\nRISULTATO: ci sono passi da sistemare. Leggi le righe ERRORE/ATTENZIONE sopra.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
