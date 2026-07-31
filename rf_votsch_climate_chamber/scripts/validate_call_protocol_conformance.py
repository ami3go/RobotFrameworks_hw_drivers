#!/usr/bin/env python3
from pathlib import Path
import inspect, sys, yaml
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from rf_votsch_climate_chamber.library import VotschClimateChamberLibrary
inv=yaml.safe_load((ROOT/'tests/conformance/data/keyword_inventory.yaml').read_text())['keywords']
vectors=yaml.safe_load((ROOT/'tests/conformance/data/protocol_vectors.yaml').read_text())['vectors']
exclusions=yaml.safe_load((ROOT/'tests/conformance/data/exclusions.yaml').read_text())['exclusions']
runtime={getattr(fn,'robot_name') for _,fn in inspect.getmembers(VotschClimateChamberLibrary,inspect.isfunction) if getattr(fn,'robot_name',None)}
inv_names={x['keyword'] for x in inv}; vector_ids={x['id'] for x in vectors}; excluded={x['keyword'] for x in exclusions}
errors=[]
if runtime!=inv_names: errors.append(f'inventory mismatch missing={sorted(runtime-inv_names)} extra={sorted(inv_names-runtime)}')
for item in inv:
    if item['device_facing'] and item.get('protocol_vector') not in vector_ids and item['keyword'] not in excluded:
        errors.append(f"{item['keyword']} has no protocol vector or exclusion")
if errors: print('\n'.join(errors)); sys.exit(1)
print(f'PASS: RFDS-019 static coverage {len(inv_names)}/{len(runtime)} keywords, {len(vector_ids)} vectors')
