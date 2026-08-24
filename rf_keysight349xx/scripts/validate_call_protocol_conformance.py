from pathlib import Path
import sys
import yaml
root = Path(__file__).resolve().parents[1]
inv = yaml.safe_load((root / "tests/conformance/data/keyword_inventory.yaml").read_text())
vec = yaml.safe_load((root / "tests/conformance/data/protocol_vectors.yaml").read_text())
entries = inv.get("keywords", [])
vector_ids = {item.get("id") for item in vec.get("vectors", [])}
missing = []
for entry in entries:
    keyword = entry.get("keyword", "<unnamed>"); facing = bool(entry.get("device_facing")); vector = entry.get("protocol_vector")
    if facing and not vector: missing.append(f"{keyword}: device-facing keyword has no vector")
    elif facing and vector not in vector_ids: missing.append(f"{keyword}: missing vector {vector}")
if missing:
    print("CONFORMANCE STATIC FAIL")
    for item in missing: print(" -", item)
    sys.exit(1)
print(f"CONFORMANCE STATIC PASS: {len(entries)} keywords inventoried; {len(vector_ids)} vectors")
