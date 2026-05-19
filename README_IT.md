# OBS Auto-Drop Visual Agent

Questa app locale per Windows controlla OBS via WebSocket e mostra clip MP4 green-screen sopra Synesthesia nei momenti musicali piu' forti. Durante lo show non usa internet, cloud, LLM, telemetria o server remoti.

## Avvio semplice

1. Fai doppio click su `setup.bat`.
2. Quando richiesto, apri OBS.
3. Segui una istruzione alla volta.
4. Fai doppio click su `run_doctor.bat` per controllare OBS, audio e clip.
5. Prima dello show usa `run_dry_mode.bat` per vedere i rilevamenti senza far partire clip automatiche.
6. Solo dopo una prova ok usa `run_agent.bat`.

## Preparare le clip

Usa `normalize_clip.bat` per aprire una pagina locale dove trascinare una o molte clip. Il tool controlla e converte nel formato consigliato:

- MP4
- H.264
- 1920x1080
- 60 fps
- senza audio

Poi usa `run_clip_marker.bat` per aprire una mini pagina locale: guardi la clip, vai nel punto esatto del drop, premi `Questo e' il drop` e poi `Salva nel manifest`.

Flusso consigliato:

1. Fai doppio click su `normalize_clip.bat`.
2. Il browser si apre su `http://127.0.0.1:8791`.
3. Trascina una o molte clip nella pagina.
4. Scegli la categoria: `drop`, `random`, `peak`, `calm` o `test`.
5. Premi `Normalizza clip selezionate`.
6. Trascina la clip pronta su `run_clip_marker.bat`.
7. Salva `impact_ms` nel manifest.

## Flip e reverse

Usa `transform_clip.bat` per aprire una pagina locale su `http://127.0.0.1:8792`.

Puoi trascinare una o molte clip e scegliere:

- flip orizzontale;
- flip verticale;
- reverse;
- anche combinazioni, per esempio flip orizzontale + reverse.

Il tool salva gli output in `clips/transformed` di default, oppure nella categoria che scegli.

## Cosa deve vedere Lorenzo

- OBS con una scena `SHOW_MAIN`.
- Synesthesia dentro OBS tramite `BG_SYNES_SPOUT`.
- Una sorgente video `OVERLAY_VIDEO` nascosta quando non serve.
- Un filtro green-screen `KEY_GREEN` su `OVERLAY_VIDEO`.
- Dashboard locale su `http://127.0.0.1:8787`.

## Regola importante

Se qualcosa non funziona, non modificare Python. Usa `run_doctor.bat` e copia l'errore esatto.
