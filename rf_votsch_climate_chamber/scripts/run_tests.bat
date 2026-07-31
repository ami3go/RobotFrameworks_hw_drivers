@echo off
cd /d "%~dp0.."
python -m pytest --cov=rf_votsch_climate_chamber --cov-branch
exit /b %errorlevel%
