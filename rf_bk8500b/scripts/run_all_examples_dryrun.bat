@echo off
setlocal
cd /d "%~dp0.."
set "PYTHON=python"
if exist ".venv\Scripts\python.exe" set "PYTHON=.venv\Scripts\python.exe"
"%PYTHON%" scripts\run_all_examples.py
exit /b %errorlevel%
