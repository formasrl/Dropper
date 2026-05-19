@echo off
setlocal
cd /d "%~dp0"
echo [Normalizzatore] Apro la UI locale con drag-and-drop multiplo.
if not exist ".venv\Scripts\activate.bat" (
  echo ERRORE: ambiente non trovato. Prima fai doppio click su setup.bat.
  pause
  exit /b 1
)
call ".venv\Scripts\activate.bat"
python scripts\clip_normalizer_ui.py
pause
