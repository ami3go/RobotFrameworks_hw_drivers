@echo off
setlocal
cd /d "%~dp0.."
set "PYTHON=python"
if exist ".venv\Scripts\python.exe" set "PYTHON=.venv\Scripts\python.exe"
"%PYTHON%" scripts\verify_project_structure.py
if errorlevel 1 exit /b %errorlevel%
"%PYTHON%" scripts\build_release.py
exit /b %errorlevel%
