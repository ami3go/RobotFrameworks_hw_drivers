@echo off
setlocal
set "ROOT=%~dp0.."
set "VENV=%ROOT%\.venv"
set "PY=%VENV%\Scripts\python.exe"

if not exist "%PY%" (
  echo Creating driver virtual environment: %VENV%
  where py >nul 2>nul
  if not errorlevel 1 (
    py -3 -m venv "%VENV%"
  ) else (
    python -m venv "%VENV%"
  )
  if errorlevel 1 exit /b 1
)

"%PY%" -m pip install --upgrade pip || exit /b 1
pushd "%ROOT%"
"%PY%" -m pip install -e ".[dev]"
set "RC=%ERRORLEVEL%"
popd
if not "%RC%"=="0" exit /b %RC%
"%PY%" -c "import robot, serial, bk8500_load" || exit /b 1
echo Environment ready: %PY%
