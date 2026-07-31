import json
from pathlib import Path

from bk8500b import BK8500B, DriverConfig

with BK8500B(DriverConfig(port="COM5")) as load:
    report = load.diagnostic_snapshot().to_dict()

Path("bk8500b-diagnostic.json").write_text(json.dumps(report, indent=2))
