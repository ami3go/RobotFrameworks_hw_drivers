@echo off
setlocal
if "%~1"=="" (
  echo Usage: run_example.bat example_name_or_number [True^|False] [COM_port] [baudrate] [auto_detect]
  exit /b 2
)
set "ROOT=%~dp0.."
set "PRIVATE_PY=%ROOT%\.venv\Scripts\python.exe"
set "PY=%PRIVATE_PY%"
set "SIMULATED=%~2"
if "%SIMULATED%"=="" set "SIMULATED=True"
set "PORT=%~3"
if "%PORT%"=="" set "PORT=COM4"
set "BAUDRATE=%~4"
if "%BAUDRATE%"=="" set "BAUDRATE=9600"
set "AUTO_DETECT=%~5"
if "%AUTO_DETECT%"=="" set "AUTO_DETECT=False"
set "RF_BK8500_ROOT=%ROOT%"

if exist "%PY%" (
  "%PY%" -c "import os,sys; sys.path.insert(0,os.environ['RF_BK8500_ROOT']); import robot,serial,bk8500_load" >nul 2>nul
  if not errorlevel 1 "%PY%" -m robot --dryrun --pythonpath "%ROOT%" --output NONE --log NONE --report NONE "%ROOT%\scripts\verify_library_import.robot" >nul 2>nul
  if not errorlevel 1 "%PY%" -m robot --dryrun --pythonpath "%ROOT%" --output NONE --log NONE --report NONE "%ROOT%\examples" >nul 2>nul
  if not errorlevel 1 goto environment_ready
)
if defined VIRTUAL_ENV if exist "%VIRTUAL_ENV%\Scripts\python.exe" (
  set "PY=%VIRTUAL_ENV%\Scripts\python.exe"
  "%VIRTUAL_ENV%\Scripts\python.exe" -c "import os,sys; sys.path.insert(0,os.environ['RF_BK8500_ROOT']); import robot,serial,bk8500_load" >nul 2>nul
  if not errorlevel 1 "%VIRTUAL_ENV%\Scripts\python.exe" -m robot --dryrun --pythonpath "%ROOT%" --output NONE --log NONE --report NONE "%ROOT%\scripts\verify_library_import.robot" >nul 2>nul
  if not errorlevel 1 "%VIRTUAL_ENV%\Scripts\python.exe" -m robot --dryrun --pythonpath "%ROOT%" --output NONE --log NONE --report NONE "%ROOT%\examples" >nul 2>nul
  if not errorlevel 1 goto environment_ready
)
call "%~dp0setup_venv.bat" || exit /b 1
set "PY=%PRIVATE_PY%"

:environment_ready
for /f "delims=" %%F in ('dir /b /s "%ROOT%\examples\*%~1*.robot" 2^>nul') do (
  "%PY%" -m robot --pythonpath "%ROOT%" --outputdir "%ROOT%\results\examples\%%~nF" --variable SIMULATED:%SIMULATED% --variable PORT:%PORT% --variable BAUDRATE:%BAUDRATE% --variable AUTO_DETECT_BAUDRATE:%AUTO_DETECT% "%%~fF"
  exit /b %ERRORLEVEL%
)
echo Example "%~1" was not found.
exit /b 2
