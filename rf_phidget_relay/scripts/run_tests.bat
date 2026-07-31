@echo off
setlocal
python -m pytest
if errorlevel 1 exit /b %errorlevel%
python -m ruff check rf_phidget_relay tests

