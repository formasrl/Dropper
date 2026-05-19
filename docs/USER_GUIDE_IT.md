# Guida operatore

Questa guida e' per usare il sistema senza modificare codice.

## Primo avvio

1. Fai doppio click su `setup.bat`.
2. Quando il wizard lo chiede, apri OBS.
3. In OBS imposta Video:
   - Base Canvas: `1920x1080`
   - Output: `1920x1080`
   - FPS: `60`
4. In OBS vai su `Tools -> WebSocket Server Settings`.
5. Attiva il server WebSocket, porta `4455`, autenticazione attiva.
6. Copia la password nel wizard.
7. Esegui `run_doctor.bat`.

## Prima dello show

1. Avvia Synesthesia Pro.
2. Attiva Spout Output in Synesthesia.
3. Apri OBS e controlla la scena `SHOW_MAIN`.
4. Esegui `run_doctor.bat`.
5. Esegui `run_dry_mode.bat` per 10-20 minuti.
6. Usa `run_agent.bat` solo quando il dry mode e' stabile.

## Preparare una clip

1. Fai doppio click su `normalize_clip.bat`.
2. Il browser si apre sulla UI locale del normalizzatore.
3. Trascina una o molte clip nella pagina.
4. Scegli la categoria.
5. Premi `Normalizza clip selezionate`.
6. Il tool controlla codec, risoluzione, FPS e audio.
7. Se serve, crea una versione normalizzata MP4 H.264 1920x1080 60 fps senza audio nella cartella giusta:
   - `clips/drop`
   - `clips/random`
   - `clips/peak`
   - `clips/calm`
   - `clips/test`
8. Trascina la clip pronta su `run_clip_marker.bat`.
9. Nel browser cerca il momento esatto del drop.
10. Premi `Questo e' il drop`.
11. Premi `Salva nel manifest`.

Per clip `random` o `calm`, `impact_ms` puo' restare vuoto.

## Flip e reverse batch

1. Fai doppio click su `transform_clip.bat`.
2. Il browser si apre su `http://127.0.0.1:8792`.
3. Trascina una o molte clip nella pagina.
4. Scegli una o piu' operazioni:
   - flip orizzontale;
   - flip verticale;
   - reverse.
5. Scegli la cartella output.
6. Premi `Trasforma clip selezionate`.

Gli output sono MP4 H.264 1920x1080 60 fps senza audio, quindi sono gia' in formato adatto a OBS.

## Durante lo show

Apri il dashboard su `http://127.0.0.1:8787`.

Pulsanti utili:

- Pausa: ferma l'automazione.
- Riprendi: riattiva l'automazione.
- Nascondi overlay: spegne subito la clip.
- Test random: prova una clip non legata al drop.
- Test drop: prova una clip drop.
- Blackout: mette nero sopra tutto.
- Togli blackout: rimuove il nero.
