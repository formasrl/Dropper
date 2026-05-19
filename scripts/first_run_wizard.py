from __future__ import annotations

import getpass
from pathlib import Path

import _bootstrap  # noqa: F401

from src.config import copy_default_files, load_config, load_env_file
from src.obs_client import OBSController, OBSStatus


def pause(message: str = "Premi Invio per continuare...") -> None:
    input(message)


def write_password(env_path: Path, password: str) -> None:
    lines: list[str] = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    updated = False
    output: list[str] = []
    for line in lines:
        if line.startswith("OBS_WS_PASSWORD="):
            output.append(f"OBS_WS_PASSWORD={password}")
            updated = True
        else:
            output.append(line)
    if not updated:
        output.append(f"OBS_WS_PASSWORD={password}")
    env_path.write_text("\n".join(output) + "\n", encoding="utf-8")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    copied = copy_default_files(root)
    print("\nOBS Auto-Drop Agent - setup guidato\n")
    if copied:
        for path in copied:
            print(f"Creato: {path.name}")
    print("\nStep 1 - Apri OBS.")
    print("Cosa devi vedere: la finestra principale di OBS aperta sul laptop.")
    pause()

    print("\nStep 2 - Imposta video OBS.")
    print("In OBS vai su File -> Settings -> Video.")
    print("Metti Base Canvas 1920x1080, Output 1920x1080, FPS 60.")
    print("Poi premi Apply e OK.")
    pause("Quando hai fatto, premi Invio...")

    print("\nStep 3 - Attiva OBS WebSocket.")
    print("In OBS vai su Tools -> WebSocket Server Settings.")
    print("Attiva Enable WebSocket server, porta 4455, Enable Authentication.")
    print("Genera o copia la password.")
    password = getpass.getpass("Incolla qui la password OBS e premi Invio: ").strip()
    if password:
        write_password(root / ".env", password)
        print("Password salvata in .env.")
    else:
        print("Password vuota: il controllo OBS potrebbe fallire.")

    load_env_file(root / ".env")
    config = load_config(root / "config.yaml")
    report = OBSController(config).diagnose_connection()
    print(report.message)
    if report.detail:
        print(report.detail)
    if report.status != OBSStatus.CONNECTED:
        print("\nProssimo passo: sistema il WebSocket in OBS e poi esegui run_doctor.bat.")
        return 1

    print("\nStep 4 - Creo/controllo la scena OBS.")
    print("Ora puoi eseguire: python scripts/setup_obs_scene.py --config config.yaml")
    print("Oppure fai doppio click su run_doctor.bat per vedere cosa manca.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
