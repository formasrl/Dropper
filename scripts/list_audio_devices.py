from __future__ import annotations

import _bootstrap  # noqa: F401

from src.audio_capture import list_audio_devices


def main() -> int:
    devices = list_audio_devices()
    if not devices:
        print("ERRORE: nessun ingresso audio trovato oppure sounddevice non installato.")
        print("Prossimo passo: collega la scheda audio o esegui setup.bat.")
        return 1
    print("Ingressi audio disponibili:\n")
    for device in devices:
        print(
            f"[{device.index}] {device.name} "
            f"- canali input: {device.max_input_channels}, sample rate: {device.default_sample_rate:.0f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
