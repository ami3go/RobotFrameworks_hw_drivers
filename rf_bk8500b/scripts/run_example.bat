@echo off
setlocal
cd /d "%~dp0.."
if "%~1"=="" (
  echo Usage: scripts\run_example.bat EXAMPLE [PORT] [PORT_B]
  echo Example: scripts\run_example.bat 01 COM5
  echo Multi-load: scripts\run_example.bat 09 COM5 COM6
  exit /b 2
)
set "PYTHON=python"
if exist ".venv\Scripts\python.exe" set "PYTHON=.venv\Scripts\python.exe"
set "EXAMPLE=%~1"
if "%EXAMPLE:~0,2%"=="09" (
  "%PYTHON%" scripts\run_example.py "%EXAMPLE%" --port-a "%~2" --port-b "%~3"
) else (
  "%PYTHON%" scripts\run_example.py "%EXAMPLE%" --port "%~2"
)
exit /b %errorlevel%
