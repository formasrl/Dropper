# OBS Auto-Drop Visual Agent

Local Windows scaffold for an OBS-controlled visual agent. It listens to local DJ audio, detects rare high-confidence build/drop moments, and pre-rolls green-screen MP4 overlays so their `impact_ms` can land near the estimated drop.

Runtime rules:

- OBS WebSocket only on `127.0.0.1:4455`.
- Dashboard only on `127.0.0.1`.
- No cloud calls, telemetry, analytics, remote servers, or runtime downloads.
- Synesthesia is not controlled by this app. OBS receives Synesthesia through Spout.

## Quick Start

1. Run `setup.bat`.
2. Open OBS when the wizard asks.
3. Follow the Italian setup prompts one step at a time.
4. Run `run_doctor.bat`.
5. Use `run_dry_mode.bat` before enabling the real show agent.

Manual commands:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
copy config.example.yaml config.yaml
copy clips_manifest.example.json clips_manifest.json
python scripts/first_run_wizard.py
python scripts/setup_obs_scene.py --config config.yaml
python scripts/validate_obs_setup.py --config config.yaml
python scripts/validate_clips.py --manifest clips_manifest.json
python -m src.app --config config.yaml --manifest clips_manifest.json --mode dry
```

## Project Shape

- `src/`: runtime modules.
- `scripts/`: guided setup and validation tools.
- `docs/`: Italian operator documentation.
- `tests/`: unit tests for non-OBS logic.
- `clips/`: local MP4 library, ignored by Git.

See `README_IT.md` and `docs/USER_GUIDE_IT.md` for operator-facing instructions.

## Clip Tools

- `normalize_clip.bat`: opens a localhost drag-and-drop UI for one or many videos, then validates/converts them to MP4 H.264, 1920x1080, 60 fps, no audio.
- `run_clip_marker.bat`: opens a localhost timeline marker in the browser where the operator can click the visual drop and save `impact_ms` to the manifest.
- `transform_clip.bat`: opens a localhost batch UI for horizontal flip, vertical flip, and reverse.

Manual equivalents:

```powershell
python scripts/normalize_clip.py path\to\clip.mov --category drop
python scripts/clip_normalizer_ui.py
python scripts/clip_transform_ui.py
python scripts/clip_marker.py clips\drop\clip_normalized.mp4 --category drop
```
