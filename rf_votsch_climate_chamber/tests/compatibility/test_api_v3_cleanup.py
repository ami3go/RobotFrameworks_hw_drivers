"""API 3 cleanup regression tests."""
from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path

from rf_votsch_climate_chamber.library import VotschClimateChamberLibrary
from rf_votsch_climate_chamber.version import API_VERSION

ROOT = Path(__file__).resolve().parents[2]
REMOVED_KEYWORDS = {
    "Connect Climate Chamber",
    "Disconnect Climate Chamber",
    "Get Climate Chamber Temperature",
    "Set Climate Chamber Temperature",
    "Start Climate Chamber",
    "Stop Climate Chamber",
}


def _runtime_keywords() -> set[str]:
    return {
        str(getattr(function, "robot_name"))
        for _, function in inspect.getmembers(VotschClimateChamberLibrary, inspect.isfunction)
        if getattr(function, "robot_name", None)
    }


def test_api_major_records_breaking_cleanup() -> None:
    assert API_VERSION == "3.0.0"


def test_removed_legacy_keywords_are_not_exported() -> None:
    assert _runtime_keywords().isdisjoint(REMOVED_KEYWORDS)
    assert all(not name.startswith("Climate Chamber ") for name in _runtime_keywords())


def test_duplicate_legacy_python_package_is_removed() -> None:
    assert not (ROOT / "votsch_climate_chamber").exists()
    assert importlib.util.find_spec("votsch_climate_chamber") is None


def test_no_deprecated_runtime_tags_remain() -> None:
    for _, function in inspect.getmembers(VotschClimateChamberLibrary, inspect.isfunction):
        assert "rfds:deprecated" not in getattr(function, "robot_tags", ())
