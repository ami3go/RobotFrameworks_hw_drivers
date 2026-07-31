@echo off
setlocal
set "ROOT=%~dp0.."
set "PRIVATE_PY=%ROOT%\.venv\Scripts\python.exe"
set "PY=%PRIVATE_PY%"
set "SIMULATED=%~1"
if "%SIMULATED%"=="" set "SIMULATED=True"
set "PORT=%~2"
if "%PORT%"=="" set "PORT=COM4"
set "RF_BK8500_ROOT=%ROOT%"

if exist "%PY%" (
  "%PY%" -c "import os,sys; sys.path.insert(0,os.environ['RF_BK8500_ROOT']); import robot,serial,bk8500_load" >nul 2>nul
  if not errorlevel 1 goto environment_ready
)
if defined VIRTUAL_ENV if exist "%VIRTUAL_ENV%\Scripts\python.exe" (
  set "PY=%VIRTUAL_ENV%\Scripts\python.exe"
  "%VIRTUAL_ENV%\Scripts\python.exe" -c "import os,sys; sys.path.insert(0,os.environ['RF_BK8500_ROOT']); import robot,serial,bk8500_load" >nul 2>nul
  if not errorlevel 1 goto environment_ready
)
call "%~dp0setup_venv.bat" || exit /b 1
set "PY=%PRIVATE_PY%"

:environment_ready
"%PY%" -m robot --pythonpath "%ROOT%" --outputdir "%ROOT%\results\examples" --variable SIMULATED:%SIMULATED% --variable PORT:%PORT% "%ROOT%\examples"
exit /b %ERRORLEVEL%
