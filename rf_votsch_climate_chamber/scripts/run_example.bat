@echo off
setlocal
cd /d "%~dp0.."
python scripts\run_example.py %*
exit /b %ERRORLEVEL%
