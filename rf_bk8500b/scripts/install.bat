@echo off
setlocal
cd /d "%~dp0.."
python -m pip install --upgrade pip
if errorlevel 1 exit /b %errorlevel%
python -m pip install .
exit /b %errorlevel%
