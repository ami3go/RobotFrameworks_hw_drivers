.PHONY: install lint type test robot examples docs build verify clean

install:
	python -m pip install -e ".[dev]"

lint:
	python -m ruff check .

type:
	python -m mypy votsch_climate_chamber

test:
	python -m pytest --cov=votsch_climate_chamber --cov-report=term-missing

robot:
	python -m robot --pythonpath . --outputdir results tests/robot

examples:
	python -m robot --dryrun --pythonpath . --outputdir results-examples examples

docs:
	python -m robot.libdoc votsch_climate_chamber.robot_library.VotschClimateChamberLibrary docs/VotschClimateChamberLibrary.html

build:
	python -m build
	python -m twine check dist/*

verify: lint type test robot examples docs build

clean:
	rm -rf build dist *.egg-info .coverage htmlcov results results-examples
