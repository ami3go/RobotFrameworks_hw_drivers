# Release Procedure

The archive naming convention is mandatory:

```text
rf_votsch_climate_chamber_vYY.RR.zip
└── rf_votsch_climate_chamber/
```

The internal root never contains a version. This allows a newer archive to replace the current project folder after local changes are committed or backed up.

## Steps

1. Update `votsch_climate_chamber/version.py`.
2. Update `pyproject.toml` with the PEP 440 version.
3. Add `history/vYY.RR.md`.
4. Add `review/vYY.RR_code_review.md`.
5. Update `CHANGELOG.md`, `README.md`, and GitHub Pages content.
6. Update or add examples and tests.
7. Run:

```bash
python scripts/validate_project_layout.py
python -m ruff check .
python -m mypy votsch_climate_chamber
python -m pytest --cov=votsch_climate_chamber --cov-report=term-missing
python -m robot --pythonpath . --outputdir results tests/robot
python -m robot --dryrun --pythonpath . --outputdir results/examples examples
python -m mkdocs build --strict
python -m build
python -m twine check dist/*
```

8. Create the archive:

```bash
python scripts/build_release.py
```

9. Verify the archive listing starts with `rf_votsch_climate_chamber/` and contains no alternate top-level directory.
10. Record SHA-256 checksum and hardware-validation status.
