from __future__ import annotations

from pathlib import Path
import hashlib
import sys

import yaml

root = Path(__file__).resolve().parents[1]
contract_path = root / "ai/ai_contract.yaml"
lock_path = root / "ai/ai_contract.lock"
contract_bytes = contract_path.read_bytes()
actual = hashlib.sha256(contract_bytes).hexdigest()
parts = lock_path.read_text(encoding="utf-8").strip().split()
expected = parts[-1] if parts else ""
errors: list[str] = []
if actual != expected:
    errors.append("contract lock mismatch")

data = yaml.safe_load(contract_bytes)
required_sections = {"identity","mental_model","state_machine","resources_consumed_provided","dependencies","capabilities","error_catalogue","safety_rules","verification_objectives","setup_teardown_contract","limitations","planning_hints","unknown_handling","conformance_rules"}
for name in sorted(required_sections - set(data or {})):
    errors.append(f"missing RFDS-017 mandatory section: {name}")
mandatory_cap_fields = {"keyword","signature","purpose","inputs","outputs","preconditions","postconditions","side_effects","risk_level","timing","stabilization_delay_s","retry_policy","errors","exclusive_resources"}
capabilities = data.get("capabilities", []) if isinstance(data, dict) else []
cap_names = []
for i, item in enumerate(capabilities):
    if not isinstance(item, dict):
        errors.append(f"capabilities[{i}] is not a mapping")
        continue
    cap_names.append(item.get("keyword"))
    missing = mandatory_cap_fields - set(item)
    for field in sorted(missing):
        errors.append(f"{item.get('keyword', i)} missing capability field: {field}")
api = yaml.safe_load((root / "api/public_api.yaml").read_text(encoding="utf-8"))
api_names = [item["keyword"] for item in api.get("keywords", [])]
if len(cap_names) != len(set(cap_names)):
    errors.append("duplicate keyword capability entries")
if set(cap_names) != set(api_names):
    errors.append(f"AI/API keyword mismatch: missing={sorted(set(api_names)-set(cap_names))}, stale={sorted(set(cap_names)-set(api_names))}")
if errors:
    print("AI CONTRACT FAIL")
    for item in errors: print(" -", item)
    sys.exit(1)
print(f"AI CONTRACT PASS: {len(cap_names)} keyword capabilities synchronized; lock {actual[:12]}...")
