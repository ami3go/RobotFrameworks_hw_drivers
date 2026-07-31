@echo off
setlocal
set "ROOT=%~dp0.."
set "PORT=%~1"
if "%PORT%"=="" set "PORT=COM9"
set "BAUDRATE=%~2"
if "%BAUDRATE%"=="" set "BAUDRATE=9600"
set "AUTO_DETECT=%~3"
if "%AUTO_DETECT%"=="" set "AUTO_DETECT=false"
set "BAUDRATE_CANDIDATES=%~4"
if "%BAUDRATE_CANDIDATES%"=="" set "BAUDRATE_CANDIDATES=4800,9600,19200,38400"
set "PROBE_TIMEOUT=%~5"
if "%PROBE_TIMEOUT%"=="" set "PROBE_TIMEOUT=0.75"
call "%~dp0setup_venv.bat"
if errorlevel 1 exit /b %errorlevel%
if not exist "%ROOT%\results\hardware_conformance" mkdir "%ROOT%\results\hardware_conformance"
"%ROOT%\.venv\Scripts\python.exe" -c "import datetime,importlib.metadata,json,platform,robot; print(json.dumps({'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bk8500_load_distribution':importlib.metadata.version('bk8500-load'),'robot_framework':robot.__version__,'python':platform.python_version(),'platform':platform.platform()}, indent=2))" > "%ROOT%\results\hardware_conformance\software_versions.json"
"%ROOT%\.venv\Scripts\python.exe" -m robot --pythonpath "%ROOT%" --outputdir "%ROOT%\results\hardware_conformance" --variable "PORT:%PORT%" --variable "BAUDRATE:%BAUDRATE%" --variable "AUTO_DETECT_BAUDRATE:%AUTO_DETECT%" --variable "BAUDRATE_CANDIDATES:%BAUDRATE_CANDIDATES%" --variable "PROBE_TIMEOUT:%PROBE_TIMEOUT%" "%ROOT%\hardware_tests\01_all_library_keywords.robot"
exit /b %errorlevel%
