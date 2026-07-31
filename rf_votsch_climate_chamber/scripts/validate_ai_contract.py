#!/usr/bin/env python3
from pathlib import Path
import hashlib, inspect, sys, yaml
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from rf_votsch_climate_chamber.library import VotschClimateChamberLibrary
contract=yaml.safe_load((ROOT/'ai/ai_contract.yaml').read_text())
lock=yaml.safe_load((ROOT/'ai/ai_contract.lock').read_text())
api=yaml.safe_load((ROOT/'api/public_api.yaml').read_text())
runtime={getattr(fn,'robot_name') for _,fn in inspect.getmembers(VotschClimateChamberLibrary,inspect.isfunction) if getattr(fn,'robot_name',None)}
contract_names={x['keyword'] for x in contract['capabilities']}
api_names={x['keyword'] for x in api['keywords']}
errors=[]
if lock['sha256']!=hashlib.sha256((ROOT/'ai/ai_contract.yaml').read_bytes()).hexdigest(): errors.append('AI contract hash mismatch')
if lock['public_api_sha256']!=hashlib.sha256((ROOT/'api/public_api.yaml').read_bytes()).hexdigest(): errors.append('public API hash mismatch')
if runtime!=contract_names or runtime!=api_names: errors.append('runtime/API/AI keyword sets differ')
if errors: print('\n'.join(errors)); sys.exit(1)
print(f'PASS: RFDS-017 synchronized for {len(runtime)} keywords')
