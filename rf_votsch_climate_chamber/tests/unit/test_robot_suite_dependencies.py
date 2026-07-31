"""Static checks for Robot suite standard-library dependencies.

These tests run without Robot Framework installed.  They catch missing explicit
imports before a hardware suite reaches the bench.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def _robot_sources() -> list[Path]:
    return sorted([*ROOT.rglob("*.robot"), *ROOT.rglob("*.resource")])


def test_log_dictionary_requires_collections_library() -> None:
    offenders: list[str] = []
    for path in _robot_sources():
        text = path.read_text(encoding="utf-8")
        if "Log Dictionary" not in text:
            continue
        settings = text.split("*** Variables ***", 1)[0]
        if "Library    Collections" not in settings and "Library           Collections" not in settings:
            offenders.append(path.relative_to(ROOT).as_posix())
    assert not offenders, (
        "Robot source uses 'Log Dictionary' without importing Collections: "
        + ", ".join(offenders)
    )


def test_active_verification_suites_use_canonical_library_import() -> None:
    suites = [
        ROOT / "tests/hardware/smoke_test.robot",
        ROOT / "tests/hardware/verify_all_api.robot",
        ROOT / "tests/robot/climate_chamber_acceptance.robot",
    ]
    legacy = "votsch_climate_chamber.robot_library.VotschClimateChamberLibrary"
    offenders = [p.relative_to(ROOT).as_posix() for p in suites if legacy in p.read_text(encoding="utf-8")]
    assert not offenders, "Active suites still use the legacy library import: " + ", ".join(offenders)


REMOVED_API_2_KEYWORDS = {
    "Connect Climate Chamber",
    "Disconnect Climate Chamber",
    "Reconnect Climate Chamber",
    "Get Climate Chamber Identification",
    "Get Climate Chamber Temperature",
    "Get Climate Chamber Setpoint",
    "Set Climate Chamber Temperature",
    "Start Climate Chamber",
    "Stop Climate Chamber",
    "Stop And Disconnect Climate Chamber",
    "Wait Until Climate Chamber Is Stable",
    "Wait For Climate Chamber Dwell",
    "Climate Chamber Should Be Connected",
    "Climate Chamber Should Be Running",
    "Climate Chamber Should Be Stopped",
}


def test_active_robot_sources_do_not_call_removed_api_2_keywords() -> None:
    offenders: list[str] = []
    for path in _robot_sources():
        relative = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        for keyword_name in REMOVED_API_2_KEYWORDS:
            if keyword_name in text:
                offenders.append(f"{relative}: {keyword_name}")
    assert not offenders, "Removed API 2 keyword found in active Robot source: " + "; ".join(offenders)


def test_canonical_connect_calls_use_named_resource_argument() -> None:
    offenders: list[str] = []
    for path in _robot_sources():
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            if re.search(r"^\s*\$\{[^}]+\}\s*=\s{2,}Connect(?:\s{2,}|$)", line) is None:
                continue
            block = "\n".join(lines[index : index + 8])
            if "resource=" not in block:
                offenders.append(f"{path.relative_to(ROOT).as_posix()}:{index + 1}")
    assert not offenders, "Canonical Connect call lacks named resource argument: " + ", ".join(offenders)


def test_hardware_suites_disable_implicit_safe_shutdown_on_disconnect() -> None:
    suites = [
        ROOT / "tests/hardware/smoke_test.robot",
        ROOT / "tests/hardware/verify_all_api.robot",
    ]
    offenders = []
    required = "safe_shutdown_on_disconnect=${FALSE}"
    for path in suites:
        if required not in path.read_text(encoding="utf-8"):
            offenders.append(path.relative_to(ROOT).as_posix())
    assert not offenders, (
        "Hardware suite may alter restored chamber state during Disconnect: "
        + ", ".join(offenders)
    )
