#!/usr/bin/env python3
from pathlib import Path
try:
    from robot.libdoc import libdoc
except ImportError as exc:
    raise SystemExit('Robot Framework is required: pip install -e .') from exc
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'generated/libdoc/VotschClimateChamberLibrary.html'; out.parent.mkdir(parents=True,exist_ok=True)
libdoc('rf_votsch_climate_chamber.VotschClimateChamberLibrary',str(out))
print(out)
