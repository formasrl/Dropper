@echo off
setlocal
cd /d "%~dp0"
echo [Dry mode] Avvio senza trigger automatici su OBS.
if not exist ".venv\Scripts\activate.bat" (
  echo ERRORE: ambiente non trovato. Prima fai doppio click su setup.bat.
  pause
  exit /b 1
)
call ".venv\Scripts\activate.bat"
python -m src.app --config config.yaml --manifest clips_manifest.json --mode dry
pause
