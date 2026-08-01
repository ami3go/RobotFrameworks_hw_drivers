from __future__ import annotations
import hashlib, inspect
from pathlib import Path
import yaml
from rf_votsch_climate_chamber.library import VotschClimateChamberLibrary
from rf_votsch_climate_chamber.plugin import VotschClimateChamberPlugin

ROOT=Path(__file__).resolve().parents[2]

def runtime_names():
    return sorted(getattr(fn,"robot_name") for _,fn in inspect.getmembers(VotschClimateChamberLibrary,inspect.isfunction) if getattr(fn,"robot_name",None))

def test_public_api_matches_runtime():
    data=yaml.safe_load((ROOT/'api/public_api.yaml').read_text())
    assert sorted(x['keyword'] for x in data['keywords']) == runtime_names()

def test_ai_contract_lock():
    lock=yaml.safe_load((ROOT/'ai/votsch_climate_chamber_ai_contract.lock').read_text())
    assert lock['sha256'] == hashlib.sha256((ROOT/'ai/votsch_climate_chamber_ai_contract.yaml').read_bytes()).hexdigest()
    assert lock['keyword_count'] == len(runtime_names())

def test_conformance_inventory_matches_runtime():
    data=yaml.safe_load((ROOT/'tests/conformance/data/keyword_inventory.yaml').read_text())
    assert sorted(x['keyword'] for x in data['keywords']) == runtime_names()

def test_plugin_manifest_matches_provider():
    descriptor=VotschClimateChamberPlugin.get_descriptor()
    assert descriptor['distribution_version'] == '26.8'
    assert descriptor['provider'] == 'rf_votsch_climate_chamber.plugin:VotschClimateChamberPlugin'
