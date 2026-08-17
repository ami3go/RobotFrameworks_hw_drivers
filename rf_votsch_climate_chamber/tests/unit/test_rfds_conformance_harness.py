"""Regression tests for RFDS-019 execution ordering and isolation."""
from __future__ import annotations

import sys
import types
from pathlib import Path

from rf_votsch_climate_chamber.library import VotschClimateChamberLibrary
from tests.support.RFDSConformanceHarness import RFDSConformanceHarness


def _keyword_map(library: VotschClimateChamberLibrary):
    result = {}
    for attribute in dir(library):
        bound = getattr(library, attribute)
        function = getattr(bound, "__func__", bound)
        robot_name = getattr(function, "robot_name", None)
        if robot_name:
            result[robot_name] = bound
    return result


def test_all_inventory_keywords_are_isolated_and_callable(monkeypatch, tmp_path: Path) -> None:
    library = VotschClimateChamberLibrary(
        default_resource="SIM::conformance",
        managed_configuration_root=str(tmp_path / "profiles"),
    )
    methods = _keyword_map(library)

    class FakeBuiltIn:
        def get_library_instance(self, _name: str):
            return library

        def run_keyword(self, name: str, *args):
            return methods[name](*args)

    builtin_module = types.ModuleType("robot.libraries.BuiltIn")
    builtin_module.BuiltIn = FakeBuiltIn
    monkeypatch.setitem(sys.modules, "robot", types.ModuleType("robot"))
    monkeypatch.setitem(sys.modules, "robot.libraries", types.ModuleType("robot.libraries"))
    monkeypatch.setitem(sys.modules, "robot.libraries.BuiltIn", builtin_module)

    root = Path(__file__).resolve().parents[2]
    harness = RFDSConformanceHarness(str(root), str(tmp_path / "evidence"))
    harness.execute_all_public_keywords_through_robot()

    assert len(harness.rows) == 58
    assert {row["result"] for row in harness.rows} == {"PASS"}
    assert all("RFDS-CON-002" not in str(row["error"]) for row in harness.rows)

