@echo off
setlocal
cd /d "%~dp0.."
python scripts\verify_project_structure.py || exit /b %errorlevel%
python scripts\verify_ai_contract.py || exit /b %errorlevel%
python -m pytest || exit /b %errorlevel%
python -m robot --outputdir results\acceptance tests\robot\adapter_acceptance.robot || exit /b %errorlevel%
python scripts\run_all_examples.py --outputdir results\dryrun || exit /b %errorlevel%
python -m ruff check BK8500BLibrary tests/test_robot_library.py tests/robot/FakeBK8500BLibrary.py scripts/build_release.py scripts/run_example.py scripts/run_all_examples.py scripts/verify_project_structure.py scripts/verify_ai_contract.py scripts/verify_release_artifacts.py scripts/generate_libdoc.py tests/test_ai_contract.py || exit /b %errorlevel%
python -m compileall -q BK8500BLibrary bk8500b scripts
exit /b %errorlevel%
