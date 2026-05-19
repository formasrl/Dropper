@echo off
setlocal
cd /d "%~dp0"
echo [Doctor] Controllo OBS, audio, clip e modalita' locale...
if not exist ".venv\Scripts\activate.bat" (
  echo ERRORE: ambiente non trovato. Prima fai doppio click su setup.bat.
  pause
  exit /b 1
)
call ".venv\Scripts\activate.bat"
python scripts\doctor.py --config config.yaml --manifest clips_manifest.json
pause
