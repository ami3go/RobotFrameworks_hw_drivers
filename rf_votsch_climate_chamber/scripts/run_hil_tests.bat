@echo off
cd /d "%~dp0.."
python -m robot --outputdir results/hil --include hardware tests/hardware
exit /b %errorlevel%
