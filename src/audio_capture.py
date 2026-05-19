from __future__ import annotations

import queue
from dataclasses import dataclass
from typing import Any

from .audio_features import AudioFeatures, compute_features, silence_features


@dataclass(frozen=True)
class AudioDevice:
    index: int
    name: str
    max_input_channels: int
    default_sample_rate: float


def list_audio_devices() -> list[AudioDevice]:
    try:
        import sounddevice as sd
    except ImportError:
        return []
    devices: list[AudioDevice] = []
    for index, info in enumerate(sd.query_devices()):
        max_inputs = int(info.get("max_input_channels", 0))
        if max_inputs > 0:
            devices.append(
                AudioDevice(
                    index=index,
                    name=str(info.get("name", f"Device {index}")),
                    max_input_channels=max_inputs,
                    default_sample_rate=float(info.get("default_samplerate", 0.0)),
                )
            )
    return devices


def find_input_device(name: str | None) -> int | None:
    devices = list_audio_devices()
    if name is None:
        return devices[0].index if devices else None
    lowered = name.lower()
    for device in devices:
        if lowered in device.name.lower():
            return device.index
    return None


class AudioCapture:
    def __init__(
        self,
        *,
        input_device_name: str | None,
        sample_rate: int,
        block_size: int,
        channels: int,
    ) -> None:
        self.input_device_name = input_device_name
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.channels = channels
        self._stream: Any | None = None
        self._queue: queue.Queue[Any] = queue.Queue(maxsize=8)
        self._previous_spectrum: Any | None = None
        self._previous_rms: float | None = None

    def start(self) -> None:
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError("sounddevice non e' installato. Esegui setup.bat.") from exc
        device = find_input_device(self.input_device_name)
        if device is None:
            raise RuntimeError("Nessun ingresso audio trovato. Collega la scheda audio e rilancia.")

        def callback(indata: Any, frames: int, time_info: Any, status: Any) -> None:
            del frames, time_info
            if status:
                pass
            try:
                self._queue.put_nowait(indata.copy())
            except queue.Full:
                _ = self._queue.get_nowait()
                self._queue.put_nowait(indata.copy())

        self._stream = sd.InputStream(
            device=device,
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            channels=self.channels,
            callback=callback,
        )
        self._stream.start()

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def read_features(self) -> AudioFeatures:
        try:
            block = self._queue.get_nowait()
        except queue.Empty:
            return silence_features()
        features, spectrum = compute_features(
            block,
            self.sample_rate,
            previous_spectrum=self._previous_spectrum,
            previous_rms=self._previous_rms,
        )
        self._previous_spectrum = spectrum
        self._previous_rms = features.rms
        return features
