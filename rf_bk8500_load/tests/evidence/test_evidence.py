"""RFDS-008 evidence engine tests (§37: schema/correlation/ordering/redaction/integrity).

Scoped to what bk8500_load's evidence.py actually produces -- see
docs/logging_and_evidence.md's "what this system deliberately does not do".
Uses the bundled SimulatedTransport (via ``simulated=True``) rather than a
hand-rolled fake, matching this driver's existing test conventions.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

from bk8500_load.exceptions import BK8500ValidationError
from bk8500_load.library import BK8500Library

_SCRIPTS_DIR = Path(__file__).parents[2] / "scripts"


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_evidence", _SCRIPTS_DIR / "validate_evidence.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_root(tmp_path) -> Path:
    session_root = tmp_path / "results" / "session" / "bk8500_load"
    run_dirs = sorted(session_root.iterdir())
    assert run_dirs, "no evidence run directory was created"
    return run_dirs[-1]


@pytest.fixture
def load(tmp_path, monkeypatch):
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    library = BK8500Library(auto_connect=False)
    library.open_load_connection(simulated=True, model="8500", alias="hardware")
    yield library, tmp_path


# ---------------------------------------------------------------------------
# Structure and manifest integrity
# ---------------------------------------------------------------------------

def test_close_all_finalizes_a_complete_evidence_run(load):
    library, tmp_path = load
    library.set_load_mode("CC")
    library.close_all_load_connections()
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
        "integrity/checksums.sha256",
    ):
        assert (root / expected).exists(), f"missing {expected}"

    summary = json.loads((root / "run_summary.json").read_text())
    assert summary["schema"] == "rfds.run_summary"
    assert summary["final_status"] == "PASS"
    assert summary["driver_id"] == "bk8500_load"

    identity = json.loads((root / "device_identity.json").read_text())
    assert identity["connections"]["hardware"]["simulated"] is True
    assert identity["connections"]["hardware"]["model"] == "8500"


def test_manifest_hashes_match_files_on_disk(load):
    library, tmp_path = load
    library.set_load_mode("CV")
    library.close_all_load_connections()
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


def test_manifest_lists_every_file_under_the_run_root(load):
    library, tmp_path = load
    library.close_all_load_connections()
    root = _run_root(tmp_path)
    manifest = json.loads((root / "evidence_manifest.json").read_text())
    listed = {entry["path"] for entry in manifest["artifacts"]}
    on_disk = {
        str(p.relative_to(root)).replace("\\", "/")
        for p in root.rglob("*")
        if p.is_file() and p.name not in ("evidence_manifest.json", "checksums.sha256")
    }
    assert listed == on_disk


# ---------------------------------------------------------------------------
# JSONL correctness and protocol frame tracing
# ---------------------------------------------------------------------------

def test_jsonl_streams_are_valid_and_gap_free(load):
    library, tmp_path = load
    library.set_load_mode("CC")
    library.set_load_setpoint("CC", 0.05)
    with pytest.raises(BK8500ValidationError):
        library.set_load_mode("NOT_A_MODE")
    library.close_all_load_connections()
    root = _run_root(tmp_path)

    for jsonl_path in root.rglob("*.jsonl"):
        sequences = []
        for line in jsonl_path.read_text().splitlines():
            record = json.loads(line)
            sequences.append(record["sequence"])
        assert sequences == list(range(1, len(sequences) + 1)), jsonl_path


def test_protocol_exchanges_carry_raw_frame_hex(load):
    library, tmp_path = load
    library.set_load_mode("CC")
    library.close_all_load_connections()
    root = _run_root(tmp_path)
    exchanges = [json.loads(line) for line in (root / "protocol" / "exchanges.jsonl").read_text().splitlines()]
    assert exchanges, "expected at least one traced frame"
    outbound = [e for e in exchanges if e["direction"] == "outbound"]
    assert outbound
    for exchange in outbound:
        assert exchange["frame_hex"] is not None
        # 26-byte frame -> 52 hex characters.
        assert len(exchange["frame_hex"]) == 52
        assert exchange["operation"].startswith("cmd=0x")


def test_nested_operations_share_one_correlation_id(load):
    """Close All Load Connections calls Close Load Connection internally."""
    library, tmp_path = load
    library.close_all_load_connections()
    root = _run_root(tmp_path)
    operations = [json.loads(line) for line in (root / "events" / "operations.jsonl").read_text().splitlines()]
    outer = next(op for op in operations if op["capability"] == "Close All Load Connections")
    inner = next(op for op in operations if op["capability"] == "Close Load Connection")
    assert outer["correlation_id"] == inner["correlation_id"]
    assert outer["operation_id"] != inner["operation_id"]


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------

def test_redact_mapping_masks_sensitive_keys():
    from bk8500_load import evidence as evidence_module

    redacted = evidence_module.redact_mapping({"mode": "CC", "password": "hunter2", "auth_token": "abc"})
    assert redacted["mode"] == "CC"
    assert redacted["password"] == {"value": "<REDACTED>", "redacted": True, "reason": "credential"}
    assert redacted["auth_token"]["redacted"] is True


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

def test_error_is_recorded_with_expected_category(load):
    library, tmp_path = load
    with pytest.raises(BK8500ValidationError):
        library.set_load_mode("NOT_A_MODE")
    library.close_all_load_connections()
    root = _run_root(tmp_path)
    errors = [json.loads(line) for line in (root / "events" / "errors.jsonl").read_text().splitlines()]
    assert len(errors) == 1
    assert errors[0]["category"] == "VALIDATION"

    summary = json.loads((root / "run_summary.json").read_text())
    assert summary["error_count"] == 1
    assert summary["final_status"] == "PASS"  # close itself still succeeded


# ---------------------------------------------------------------------------
# NullEvidenceRun / evidence_enabled=False
# ---------------------------------------------------------------------------

def test_evidence_disabled_writes_nothing_to_disk(tmp_path, monkeypatch):
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    library = BK8500Library(auto_connect=False, evidence_enabled=False)
    library.open_load_connection(simulated=True, model="8500", alias="hardware")
    library.set_load_mode("CC")
    library.close_all_load_connections()
    assert not (tmp_path / "results").exists()


def test_evidence_disabled_export_diagnostic_bundle_returns_none(tmp_path, monkeypatch):
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    library = BK8500Library(auto_connect=False, evidence_enabled=False)
    library.open_load_connection(simulated=True, model="8500", alias="hardware")
    assert library.export_diagnostic_bundle() is None
    library.close_all_load_connections()


# ---------------------------------------------------------------------------
# Export Diagnostic Bundle
# ---------------------------------------------------------------------------

def test_export_diagnostic_bundle_produces_a_readable_zip(load):
    library, _tmp_path = load
    library.set_load_mode("CC")
    bundle_path = library.export_diagnostic_bundle()
    assert bundle_path is not None
    archive_path = Path(bundle_path)
    assert archive_path.exists()

    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        assert any(name.endswith("environment.json") for name in names)
        assert any(name.endswith("events/operations.jsonl") for name in names)
    library.close_all_load_connections()


def test_export_diagnostic_bundle_honors_explicit_destination(load):
    library, tmp_path = load
    destination = tmp_path / "custom" / "bundle.zip"
    result = library.export_diagnostic_bundle(str(destination))
    assert Path(result) == destination
    assert destination.exists()
    library.close_all_load_connections()


def test_evidence_survives_multiple_aliases_and_tags_them_separately(load):
    library, tmp_path = load
    library.open_load_connection(simulated=True, model="8500", alias="secondary")
    library.switch_load_connection("secondary")
    library.set_load_mode("CV")
    library.switch_load_connection("hardware")
    library.set_load_mode("CC")
    library.close_all_load_connections()
    root = _run_root(tmp_path)
    operations = [json.loads(line) for line in (root / "events" / "operations.jsonl").read_text().splitlines()]
    aliases = {op["session_alias"] for op in operations if op["capability"] == "Set Load Mode"}
    assert aliases == {"hardware", "secondary"}
    identity = json.loads((root / "device_identity.json").read_text())
    assert set(identity["connections"]) == {"hardware", "secondary"}


# ---------------------------------------------------------------------------
# validate_evidence.py
# ---------------------------------------------------------------------------

def test_validate_evidence_script_accepts_a_clean_run(load):
    library, tmp_path = load
    library.set_load_mode("CC")
    library.close_all_load_connections()
    root = _run_root(tmp_path)
    validator = _load_validator()
    assert validator.validate(root) == []


def test_validate_evidence_script_detects_tampering(load):
    library, tmp_path = load
    library.close_all_load_connections()
    root = _run_root(tmp_path)
    events_path = root / "events" / "events.jsonl"
    with events_path.open("a") as handle:
        handle.write("this is not json\n")
    validator = _load_validator()
    findings = validator.validate(root)
    assert any("HASH MISMATCH" in finding and "events.jsonl" in finding for finding in findings)
    assert any("invalid JSON" in finding for finding in findings)


def test_validate_evidence_script_detects_missing_manifest_entry(load):
    library, tmp_path = load
    library.close_all_load_connections()
    root = _run_root(tmp_path)
    (root / "attachments" / "extra_note.txt").write_text("not tracked")
    validator = _load_validator()
    findings = validator.validate(root)
    assert any("FILE NOT IN MANIFEST" in finding for finding in findings)
