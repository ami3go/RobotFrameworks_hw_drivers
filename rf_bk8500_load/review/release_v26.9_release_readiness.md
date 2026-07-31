# Release readiness — rf_bk8500_load_v26.9

## Acceptance criteria

- Flat root layout retained: PASS
- AI folder retained and locked: PASS
- Public shim defines the library class locally: PASS
- Required connection keyword metadata present: PASS
- Dry-run import smoke suite delivered and wired into launchers: PASS
- Python unit/contract/structure suite: PASS
- Wheel and ZIP build: PASS
- Physical COM9 hardware run: OPEN

## Release decision

Ready for v26.9 distribution. The user should replace the complete v26.8
folder to avoid retaining an older editable installation or stale `.venv`.
