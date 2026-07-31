@echo off
cd /d "%~dp0.."
python scripts/generate_libdoc.py
exit /b %errorlevel%
