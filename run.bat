@echo off
REM Saathi - one command for Windows:  double-click run.bat  (or type run.bat)
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python 3 is not installed. Get it from https://www.python.org/downloads/ and tick "Add to PATH".
  pause
  exit /b 1
)

if not exist .venv (
  echo First run: setting up, about 30 seconds...
  python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install -q --disable-pip-version-check -r requirements.txt

if "%PORT%"=="" set PORT=8000
start "" cmd /c "timeout /t 2 >nul & start http://localhost:%PORT%"
python backend\main.py
pause
