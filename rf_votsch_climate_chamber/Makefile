.PHONY: test lint typecheck conformance examples docs package clean

test:
	python -m pytest --cov=rf_votsch_climate_chamber --cov-branch

lint:
	python -m ruff check rf_votsch_climate_chamber tests scripts

typecheck:
	python -m mypy rf_votsch_climate_chamber

conformance:
	python scripts/run_conformance.py

examples:
	python scripts/run_all_examples.py --dry-run

docs:
	python scripts/generate_libdoc.py

package:
	python scripts/build_release.py

clean:
	python -c "import shutil,pathlib; [shutil.rmtree(p,ignore_errors=True) for p in map(pathlib.Path,['build','dist','.pytest_cache','.mypy_cache','.ruff_cache'])]"
