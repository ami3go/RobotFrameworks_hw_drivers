@echo off
setlocal
if "%~1"=="" (
  echo Usage: run_example.bat examples\02_single_channel.robot
  exit /b 2
)
python -m robot --outputdir results "%~1"

