@echo off
setlocal
cd /d "%~dp0.."
python scripts\verify_project_structure.py || exit /b %errorlevel%
python scripts\verify_ai_contract.py || exit /b %errorlevel%
python -m pip install --upgrade build twine || exit /b %errorlevel%
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
for /d %%D in (*.egg-info) do rmdir /s /q "%%D"
python scripts\generate_libdoc.py || exit /b %errorlevel%
python -m build || exit /b %errorlevel%
python -m twine check dist\* || exit /b %errorlevel%
python scripts\verify_release_artifacts.py || exit /b %errorlevel%
python scripts\build_release.py
exit /b %errorlevel%
