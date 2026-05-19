from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .utils import clamp01


@dataclass(frozen=True)
class AudioFeatures:
    rms: float = 0.0
    bass_energy: float = 0.0
    low_mid_energy: float = 0.0
    high_energy: float = 0.0
    spectral_flux: float = 0.0
    bass_presence: float = 1.0
    energy_slope: float = 0.0
    onset_score: float = 0.0
    bpm_estimate: float | None = None
    beat_confidence: float = 0.0
    bass_return_probability: float = 0.0
    signal_healthy: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "rms": self.rms,
            "bass_energy": self.bass_energy,
            "low_mid_energy": self.low_mid_energy,
            "high_energy": self.high_energy,
            "spectral_flux": self.spectral_flux,
            "bass_presence": self.bass_presence,
            "energy_slope": self.energy_slope,
            "onset_score": self.onset_score,
            "bpm_estimate": self.bpm_estimate,
            "beat_confidence": self.beat_confidence,
            "bass_return_probability": self.bass_return_probability,
            "signal_healthy": self.signal_healthy,
        }


def silence_features() -> AudioFeatures:
    return AudioFeatures(signal_healthy=False)


def compute_features(
    samples: Any,
    sample_rate: int,
    *,
    previous_spectrum: Any | None = None,
    rolling_bass_median: float | None = None,
    previous_rms: float | None = None,
) -> tuple[AudioFeatures, Any]:
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("numpy non e' installato. Esegui setup.bat.") from exc

    data = np.asarray(samples, dtype=np.float32)
    if data.ndim > 1:
        data = data.mean(axis=1)
    if data.size == 0:
        return silence_features(), None

    rms = float(np.sqrt(np.mean(np.square(data))))
    windowed = data * np.hanning(data.size)
    spectrum = np.abs(np.fft.rfft(windowed))
    freqs = np.fft.rfftfreq(data.size, d=1.0 / sample_rate)

    def band_energy(low: float, high: float) -> float:
        mask = (freqs >= low) & (freqs < high)
        if not np.any(mask):
            return 0.0
        return float(np.mean(spectrum[mask]))

    bass = band_energy(40, 160)
    low_mid = band_energy(160, 500)
    high = band_energy(4000, 10000)

    if previous_spectrum is None:
        flux = 0.0
    else:
        prev = np.asarray(previous_spectrum)
        length = min(prev.size, spectrum.size)
        flux = float(np.mean(np.maximum(0.0, spectrum[:length] - prev[:length])))

    median = rolling_bass_median if rolling_bass_median and rolling_bass_median > 1e-9 else bass
    bass_presence = 1.0 if median <= 1e-9 else bass / median
    slope = 0.0 if previous_rms is None else (rms - previous_rms) / max(previous_rms, 1e-6)
    onset_score = clamp01(flux / max(float(np.mean(spectrum)), 1e-6))
    bass_return_probability = clamp01((bass_presence - 0.8) / 0.7 + max(slope, 0.0) * 0.2)

    return (
        AudioFeatures(
            rms=rms,
            bass_energy=bass,
            low_mid_energy=low_mid,
            high_energy=high,
            spectral_flux=flux,
            bass_presence=bass_presence,
            energy_slope=clamp01((slope + 1.0) / 2.0) * 2.0 - 1.0,
            onset_score=onset_score,
            bpm_estimate=None,
            beat_confidence=0.0,
            bass_return_probability=bass_return_probability,
            signal_healthy=rms > 0.005,
        ),
        spectrum,
    )
