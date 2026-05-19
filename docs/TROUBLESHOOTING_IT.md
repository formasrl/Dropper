# Risoluzione problemi

## ERRORE: OBS non aperto

Apri OBS. Poi rilancia `run_doctor.bat`.

## ERRORE: OBS aperto ma WebSocket non attivo

In OBS vai su `Tools -> WebSocket Server Settings`.

Controlla:

- server attivo;
- porta `4455`;
- autenticazione attiva.

Poi rilancia `run_doctor.bat`.

## ERRORE: password OBS errata

Apri `.env` e controlla la riga:

```text
OBS_WS_PASSWORD=...
```

La password deve essere identica a quella in OBS.

## Plugin Spout2 mancante

Installa il plugin Spout2 per OBS durante il setup. Dopo l'installazione chiudi e riapri OBS.

Durante lo show non deve servire internet.

## Nessun ingresso audio

Collega la scheda audio o il mixer DJ. Poi esegui:

```powershell
python scripts/list_audio_devices.py
```

Se non compare nulla, riavvia la scheda audio e OBS.

## Clip mancanti

Esegui:

```powershell
python scripts/validate_clips.py --manifest clips_manifest.json --strict-files
```

Ogni file indicato nel manifest deve esistere.

## FFmpeg non trovato

Il normalizzatore video richiede FFmpeg.

Installa FFmpeg durante il setup, poi chiudi e riapri il terminale o rilancia `setup.bat`.

## Il browser non si apre

Il tool stampa comunque l'indirizzo locale.

Per il normalizzatore apri:

```text
http://127.0.0.1:8791
```

Per il marker drop apri:

```text
http://127.0.0.1:8790
```

Per flip/reverse apri:

```text
http://127.0.0.1:8792
```
