@echo off
setlocal
cd /d "%~dp0"
echo.
echo [Setup] Preparo OBS Auto-Drop Agent...
echo.
set "PYTHON_CMD="
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py -3.13 -c "import sys" >nul 2>nul && set "PYTHON_CMD=py -3.13"
  if not defined PYTHON_CMD py -3.12 -c "import sys" >nul 2>nul && set "PYTHON_CMD=py -3.12"
  if not defined PYTHON_CMD py -3.11 -c "import sys" >nul 2>nul && set "PYTHON_CMD=py -3.11"
)
if not defined PYTHON_CMD (
  where python >nul 2>nul && set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
  echo ERRORE: Python non trovato.
  echo Installa Python 3.11, 3.12 o 3.13 e poi rilancia setup.bat.
  pause
  exit /b 1
)
%PYTHON_CMD% -c "import sys; raise SystemExit(0 if (3,11) <= sys.version_info < (3,14) else 1)" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
  echo ERRORE: serve Python 3.11, 3.12 o 3.13.
  echo Installa Python e poi rilancia setup.bat.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Creo ambiente Python locale...
  %PYTHON_CMD% -m venv .venv
)
call ".venv\Scripts\activate.bat"
echo Installo dipendenze. Questa fase richiede internet solo durante il setup.
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist ".env" copy ".env.example" ".env" >nul
if not exist "config.yaml" copy "config.example.yaml" "config.yaml" >nul
if not exist "clips_manifest.json" copy "clips_manifest.example.json" "clips_manifest.json" >nul
echo.
echo Avvio il wizard guidato...
python scripts\first_run_wizard.py
pause
