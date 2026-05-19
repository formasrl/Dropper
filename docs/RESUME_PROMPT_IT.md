# Prompt per riprendere il lavoro

Usa questo prompt in una nuova sessione Codex quando lavori da un altro PC.

```text
Riprendi il lavoro sulla repo GitHub:

https://github.com/formasrl/Dropper

Contesto:
questa repo contiene lo scaffold di un'app Windows-local chiamata OBS Auto-Drop Visual Agent. E' pensata per un operatore non tecnico: setup guidato in italiano, OBS WebSocket, dashboard locale, doctor, normalizzatore video, marker impact_ms, tool batch per flip/reverse clip.

Stato attuale:
- branch: main
- commit iniziale gia' pushato: fa8eda1 "Initial OBS auto-drop agent scaffold"
- repo sincronizzata e working tree pulito
- esiste un `.gitignore` intenzionale: NON rimuoverlo, perche' protegge `.env`, `.venv`, config locali, log e clip video pesanti
- le clip vere non sono nella repo e vanno messe localmente in `clips/`

Prima cosa da fare:
1. Clona la repo.
2. Leggi `README_IT.md`, `docs/USER_GUIDE_IT.md`, `docs/CODEX_TASKS.md`.
3. Controlla lo stato con `git status --short --branch`.
4. Installa dipendenze con `setup.bat` oppure `pip install -r requirements.txt`.
5. Continua da Phase 0/1: test reale OBS, setup scena, validazione WebSocket, test overlay, dashboard, poi audio/dry-run.

Tool gia' presenti:
- `setup.bat`
- `run_doctor.bat`
- `run_dry_mode.bat`
- `run_agent.bat`
- `normalize_clip.bat`
- `run_clip_marker.bat`
- `transform_clip.bat`

Obiettivo prossimo:
rendere il sistema davvero operativo su OBS reale:
- configurare/validare `SHOW_MAIN`
- testare `BG_SYNES_SPOUT`, `OVERLAY_VIDEO`, `KEY_GREEN`, `FLASH_WHITE`, `BLACKOUT`
- provare una clip MP4 reale
- verificare show/hide/restart via OBS WebSocket
- poi passare ad audio input e dry-run detector

Importante:
mantieni tutto local-only:
- dashboard solo `127.0.0.1`
- OBS solo `127.0.0.1:4455`
- niente cloud, niente telemetry, niente download runtime
- UX e messaggi in italiano semplice per Lorenzo, operatore non tecnico
```
