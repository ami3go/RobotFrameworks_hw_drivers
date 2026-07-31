# Robot Framework Driver Project Requirements

This repository follows the shared Robot Framework Driver packaging convention.

## Mandatory release structure

```text
rf_votsch_climate_chamber_v26.02.zip
└── rf_votsch_climate_chamber/
    ├── history/
    ├── review/
    ├── examples/
    ├── scripts/
    ├── guide/
    ├── docs/
    ├── README.md
    └── ...
```

## Versioning

- Human/release version: `vYY.RR`, for example `v26.01`.
- ZIP filename: `rf_{driver_name}_vYY.RR.zip`.
- Fixed internal root: `rf_{driver_name}/` without a version.
- Python packaging uses the normalized PEP 440 equivalent, for example `26.1`.

## Required content

- release history for every revision;
- code review for every revision;
- at least 10 examples;
- scripts to execute examples;
- current GitHub README;
- current GitHub Pages source and deployment workflow;
- PyCharm and Robot Framework setup guide;
- installable Python package, tests, and validation evidence.

Run `python scripts/validate_project_layout.py` before creating a release.

## AI contract requirements

Every release must include `ai/ai_contract.yaml` and `ai/ai_contract.lock` conforming to RFDS-017. The public keyword manifest and lock must validate in CI. A bench-facing `system_ai_contract.yaml` conforming to RFDS-018 must be supplied as a conservative template or site-specific contract; unresolved safety-critical values must use `UNKNOWN` and disable hardware-control planning.
