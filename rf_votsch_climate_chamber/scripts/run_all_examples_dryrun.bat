@echo off
setlocal
cd /d "%~dp0.."
python -m robot --dryrun --pythonpath . --outputdir results\examples examples
exit /b %ERRORLEVEL%
