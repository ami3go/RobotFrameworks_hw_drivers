@echo off
call "%~dp0..\scripts\run_hardware_conformance.bat" %*
exit /b %errorlevel%
