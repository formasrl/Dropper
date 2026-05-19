# Codex implementation tasks

## Phase 0

- Keep setup beginner-safe and Italian-first.
- Improve `first_run_wizard.py` with visible checkpoints after OBS is connected.
- Add a test-clip picker that writes to `OVERLAY_VIDEO`.
- Expand doctor output for Spout sender status.

## Phase 1

- Add a dedicated `test_drop_clip` command.
- Measure OBS media restart timing on the target laptop.
- Inspect `GetInputSettings` for the real OBS media source and lock exact keys.

## Phase 2

- Add dashboard setup checklist cards.
- Wire dashboard test buttons to real OBS actions.
- Add clear visual state for PAUSED and BLACKOUT.

## Phase 3

- Stream live meters to the dashboard.
- Write JSONL and CSV feature logs.
- Add audio calibration windows.

## Phase 4

- Run detector in dry mode for rehearsal mixes.
- Tune conservative thresholds.

## Phase 5

- Enable sparse auto triggers.
- Run a 90-minute stability test and review logs.
