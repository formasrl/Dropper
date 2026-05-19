# Checklist OBS

## Video

- Base Canvas: `1920x1080`
- Output: `1920x1080`
- FPS: `60`
- Streaming e recording spenti, salvo necessita' esplicita.

## WebSocket

- Menu: `Tools -> WebSocket Server Settings`
- Server attivo.
- Porta: `4455`
- Authentication attiva.
- Password salvata in `.env` come `OBS_WS_PASSWORD=...`

## Scena

Scena unica: `SHOW_MAIN`

Ordine sorgenti dal basso verso l'alto:

1. `BG_SYNES_SPOUT`
2. `OVERLAY_VIDEO`
3. `FLASH_WHITE`
4. `BLACKOUT`

## Spout

Se `BG_SYNES_SPOUT` non si crea:

1. Installa il plugin Spout2 per OBS durante il setup.
2. Riapri OBS.
3. Rilancia `python scripts/setup_obs_scene.py --config config.yaml`.

## Green screen

Su `OVERLAY_VIDEO` deve esserci il filtro `KEY_GREEN`.

Valori iniziali:

- Similarity: circa `400`
- Smoothness: circa `80`
- Spill reduction: circa `100`

Regola a occhio in OBS usando una clip test.
