"""RFDS-008 live evidence engine tests for rf_votsch_climate_chamber.

Scoped to what evidence.py actually produces, mirroring the equivalent test
suite built for rf_phidget_relay. Uses the driver's own SIM:: simulator
transport rather than a fake factory.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

from rf_votsch_climate_chamber import evidence as evidence_module
from rf_votsch_climate_chamber.exceptions import DriverSafetyError
from rf_votsch_climate_chamber.library import VotschClimateChamberLibrary

_SCRIPTS_DIR = Path(__file__).parents[2] / "scripts"


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_evidence", _SCRIPTS_DIR / "validate_evidence.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_root(tmp_path) -> Path:
    session_root = tmp_path / "results" / "session" / "rf_votsch_climate_chamber"
    run_dirs = sorted(session_root.iterdir())
    assert run_dirs, "no evidence run directory was created"
    return run_dirs[-1]


@pytest.fixture
def chamber(tmp_path):
    lib = VotschClimateChamberLibrary()
    lib.connect("SIM::default", alias="default")
    yield lib, tmp_path
    if lib._registry.list_states():
        lib._registry.disconnect_all(safe_shutdown=False)
    lib._finalize_evidence()


def test_finalize_produces_a_complete_evidence_run(chamber):
    lib, tmp_path = chamber
    lib.measure_temperature()
    lib._registry.disconnect_all(safe_shutdown=False)
    lib._finalize_evidence()
    root = _run_root(tmp_path)

    for expected in (
        "run_summary.json",
        "run_summary.md",
        "environment.json",
        "device_identity.json",
        "evidence_manifest.json",
        "events/events.jsonl",
        "events/operations.jsonl",
        "protocol/exchanges.jsonl",
        "protocol/outbound_trace.log",
        "protocol/inbound_trace.log",
        "integrity/checksums.sha256",
    ):
        assert (root / expected).exists(), f"missing {expected}"

    summary = json.loads((root / "run_summary.json").read_text())
    assert summary["schema"] == "rfds.run_summary"
    assert summary["driver_id"] == "rf_votsch_climate_chamber"
    assert summary["final_status"] == "PASS"


def test_simulator_connection_is_recorded_honestly(chamber):
    """RFDS-008 6.6: a SIM:: session must never be reported as REAL_HARDWARE."""
    lib, tmp_path = chamber
    lib._registry.disconnect_all(safe_shutdown=False)
    lib._finalize_evidence()
    root = _run_root(tmp_path)
    summary = json.loads((root / "run_summary.json").read_text())
    assert summary["execution_mode"] == "SIMULATOR"


def test_manifest_hashes_match_files_on_disk(chamber):
    lib, tmp_path = chamber
    lib.get_chamber_status()
    lib._registry.disconnect_all(safe_shutdown=False)
    lib._finalize_evidence()
    root = _run_root(tmp_path)

    manifest = json.loads((root / "evidence_manifest.json").read_text())
    assert manifest["artifact_count"] == len(manifest["artifacts"]) > 0
    for entry in manifest["artifacts"]:
        data = (root / entry["path"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry["sha256"]
        assert len(data) == entry["size_bytes"]

    listed_paths = {entry["path"] for entry in manifest["artifacts"]}
    assert "evidence_manifest.json" not in listed_paths
    assert "integrity/checksums.sha256" not in listed_paths


def test_manifest_lists_every_file_under_the_run_root(chamber):
    lib, tmp_path = chamber
    lib._registry.disconnect_all(safe_shutdown=False)
    lib._finalize_evidence()
    root = _run_root(tmp_path)
    manifest = json.loads((root / "evidence_manifest.json").read_text())
    listed = {entry["path"] for entry in manifest["artifacts"]}
    on_disk = {
        str(p.relative_to(root)).replace("\\", "/")
        for p in root.rglob("*")
        if p.is_file() and p.name not in ("evidence_manifest.json", "checksums.sha256")
    }
    assert listed == on_disk


def test_protocol_exchanges_are_captured_via_the_existing_trace_observer(chamber):
    """Confirms evidence.py bridges transports/tracing.py's TraceObserver rather
    than re-instrumenting the transport layer."""
    lib, tmp_path = chamber
    lib.get_chamber_status()
    lib._registry.disconnect_all(safe_shutdown=False)
    lib._finalize_evidence()
    root = _run_root(tmp_path)
    exchanges = [
        json.loads(line)
        for line in (root / "protocol" / "exchanges.jsonl").read_text().splitlines()
    ]
    assert any(
        e["direction"] == "outbound" and "10012" in (e["data_text"] or "") for e in exchanges
    )
    assert any(e["direction"] == "inbound" and "READY" in (e["data_text"] or "") for e in exchanges)


def test_jsonl_streams_are_valid_and_gap_free(chamber):
    lib, tmp_path = chamber
    lib.get_chamber_status()
    with contextlib.suppress(DriverSafetyError):
        lib.set_temperature(9999)
    lib._registry.disconnect_all(safe_shutdown=False)
    lib._finalize_evidence()
    root = _run_root(tmp_path)

    for jsonl_path in root.rglob("*.jsonl"):
        sequences = [json.loads(line)["sequence"] for line in jsonl_path.read_text().splitlines()]
        assert sequences == list(range(1, len(sequences) + 1)), jsonl_path


def test_redact_mapping_masks_sensitive_keys():
    redacted = evidence_module.redact_mapping({"alias": "default", "password": "hunter2"})
    assert redacted["alias"] == "default"
    assert redacted["password"] == {"value": "<REDACTED>", "redacted": True, "reason": "credential"}


def test_error_is_recorded_with_this_drivers_exception_category(chamber):
    lib, tmp_path = chamber
    with pytest.raises(DriverSafetyError):
        lib.set_temperature(9999)  # DriverLimitViolationError -> outside safety limits
    lib._registry.disconnect_all(safe_shutdown=False)
    lib._finalize_evidence()
    root = _run_root(tmp_path)
    errors = [
        json.loads(line) for line in (root / "events" / "errors.jsonl").read_text().splitlines()
    ]
    assert len(errors) == 1
    assert (
        errors[0]["category"] == "SAFETY"
    )  # DriverLimitViolationError -> DriverSafetyError family

    summary = json.loads((root / "run_summary.json").read_text())
    assert summary["error_count"] == 1


def test_finalize_reports_fail_when_an_operation_recorded_an_error(chamber):
    """Regression: ``_finalize_evidence`` used to hardcode ``status="PASS"``,
    so a run with a recorded error (e.g. ``Get Dryer`` on an unconfigured
    aux-output channel) was still reported as an overall PASS."""
    lib, tmp_path = chamber
    with pytest.raises(DriverSafetyError):
        lib.set_temperature(9999)
    lib._registry.disconnect_all(safe_shutdown=False)
    lib._finalize_evidence()
    root = _run_root(tmp_path)
    summary = json.loads((root / "run_summary.json").read_text())
    assert summary["error_count"] == 1
    assert summary["final_status"] == "FAIL"


def test_evidence_disabled_writes_nothing_to_disk(tmp_path):
    lib = VotschClimateChamberLibrary(evidence_enabled=False)
    lib.connect("SIM::default", alias="default")
    lib.get_chamber_status()
    lib._registry.disconnect_all(safe_shutdown=False)
    lib._finalize_evidence()
    assert not (tmp_path / "results").exists()


def test_evidence_disabled_export_diagnostic_bundle_returns_none(tmp_path):
    lib = VotschClimateChamberLibrary(evidence_enabled=False)
    lib.connect("SIM::default", alias="default")
    assert lib.export_diagnostic_bundle() is None
    lib._registry.disconnect_all(safe_shutdown=False)


def test_export_diagnostic_bundle_produces_a_readable_zip(chamber):
    lib, tmp_path = chamber
    lib.get_chamber_status()
    bundle_path = lib.export_diagnostic_bundle()
    assert bundle_path is not None
    with zipfile.ZipFile(Path(bundle_path)) as archive:
        names = archive.namelist()
        assert any(name.endswith("environment.json") for name in names)
        assert any(name.endswith("events/operations.jsonl") for name in names)


def test_export_diagnostic_bundle_is_distinct_from_export_diagnostics(chamber):
    """Export Diagnostics (pre-existing) writes a point-in-time snapshot;
    Export Diagnostic Bundle (new) zips the append-only evidence run. Both
    must keep working independently."""
    lib, tmp_path = chamber
    snapshot_path = tmp_path / "diagnostics_snapshot.json"
    snapshot_result = lib.export_diagnostics(str(snapshot_path))
    assert Path(snapshot_result["path"]).exists()
    bundle_path = lib.export_diagnostic_bundle()
    assert bundle_path is not None
    assert Path(bundle_path).suffix == ".zip"
    assert Path(bundle_path) != Path(snapshot_result["path"])


def test_validate_evidence_script_accepts_a_clean_run(chamber):
    lib, tmp_path = chamber
    lib._registry.disconnect_all(safe_shutdown=False)
    lib._finalize_evidence()
    root = _run_root(tmp_path)
    validator = _load_validator()
    assert validator.validate(root) == []


def test_validate_evidence_script_detects_tampering(chamber):
    lib, tmp_path = chamber
    lib._registry.disconnect_all(safe_shutdown=False)
    lib._finalize_evidence()
    root = _run_root(tmp_path)
    events_path = root / "events" / "events.jsonl"
    with events_path.open("a") as handle:
        handle.write("this is not json\n")
    validator = _load_validator()
    findings = validator.validate(root)
    assert any("HASH MISMATCH" in finding and "events.jsonl" in finding for finding in findings)
    assert any("invalid JSON" in finding for finding in findings)
