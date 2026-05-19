@echo off
setlocal
cd /d "%~dp0"
echo [Clip marker] Trascina un video su questo file .bat oppure inserisci il percorso.
if not exist ".venv\Scripts\activate.bat" (
  echo ERRORE: ambiente non trovato. Prima fai doppio click su setup.bat.
  pause
  exit /b 1
)
call ".venv\Scripts\activate.bat"
set "CLIP_PATH=%~1"
if "%CLIP_PATH%"=="" (
  set /p CLIP_PATH=Percorso video: 
)
python scripts\clip_marker.py "%CLIP_PATH%"
pause
