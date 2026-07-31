@echo off
cd /d "%~dp0.."
python scripts/run_all_examples.py
exit /b %errorlevel%
