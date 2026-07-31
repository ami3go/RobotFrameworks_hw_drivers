@echo off
setlocal
set "ROOT=%~dp0.."
if "%~1"=="" (
  set "PORT=COM12"
) else (
  set "PORT=%~1"
)
call "%~dp0setup_venv.bat" >nul
"%ROOT%\.venv\Scripts\python.exe" "%ROOT%\hardware_tests\02_serial_echo_diagnostic.py" --port "%PORT%"
exit /b %ERRORLEVEL%
