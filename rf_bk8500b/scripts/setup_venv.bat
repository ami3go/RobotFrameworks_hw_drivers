@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" python -m venv .venv
if errorlevel 1 exit /b %errorlevel%
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b %errorlevel%
".venv\Scripts\python.exe" -m pip install -e ".[dev]"
if errorlevel 1 exit /b %errorlevel%
echo Environment ready. Activate with: .venv\Scripts\activate.bat
