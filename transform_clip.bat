@echo off
setlocal
cd /d "%~dp0"
echo [Transformer] Apro la UI locale per flip/reverse batch.
if not exist ".venv\Scripts\activate.bat" (
  echo ERRORE: ambiente non trovato. Prima fai doppio click su setup.bat.
  pause
  exit /b 1
)
call ".venv\Scripts\activate.bat"
python scripts\clip_transform_ui.py
pause
