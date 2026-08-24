from __future__ import annotations

import inspect
from pathlib import Path
import sys
import yaml
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rf_keysight349xx.library import Keysight349xxLibrary  # noqa: E402
api = yaml.safe_load((ROOT / "api/public_api.yaml").read_text(encoding="utf-8"))
inventory = yaml.safe_load((ROOT / "tests/conformance/data/keyword_inventory.yaml").read_text(encoding="utf-8"))
exports: dict[str, str] = {}
for cls in reversed(Keysight349xxLibrary.__mro__):
    for method_name, obj in cls.__dict__.items():
        robot_name = getattr(obj, "robot_name", None)
        if robot_name:
            if robot_name in exports and exports[robot_name] != method_name:
                raise SystemExit(f"duplicate Robot keyword after normalization: {robot_name}")
            exports[robot_name] = method_name
api_entries = {item["keyword"]: item for item in api.get("keywords", [])}
inv_entries = {item["keyword"]: item for item in inventory.get("keywords", [])}
errors: list[str] = []
for label, declared in (("api/public_api.yaml", api_entries), ("keyword_inventory.yaml", inv_entries)):
    missing = sorted(set(exports) - set(declared)); stale = sorted(set(declared) - set(exports))
    errors.extend(f"{label}: missing exported keyword {name}" for name in missing)
    errors.extend(f"{label}: stale/non-exported keyword {name}" for name in stale)
for keyword_name, method_name in exports.items():
    entry = api_entries.get(keyword_name)
    if not entry: continue
    if entry.get("python_method") != method_name:
        errors.append(f"{keyword_name}: API method {entry.get('python_method')!r} != runtime method {method_name!r}")
    obj = getattr(Keysight349xxLibrary, method_name)
    sig = inspect.signature(obj)
    params = [param for name, param in sig.parameters.items() if name != "self"]
    actual_sig = str(sig.replace(parameters=params, return_annotation=inspect.Signature.empty))
    if actual_sig != entry.get("signature"):
        errors.append(f"{keyword_name}: signature {actual_sig!r} != declared {entry.get('signature')!r}")
if errors:
    print("PUBLIC API VALIDATION FAIL")
    for item in errors: print(" -", item)
    raise SystemExit(1)
print(f"PUBLIC API VALIDATION PASS: {len(exports)} explicit Robot keywords synchronized")
