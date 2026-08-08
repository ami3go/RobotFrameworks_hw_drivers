"""RFDS-008 evidence engine tests (§37: schema/correlation/ordering/redaction/integrity)
for rf_slcan, scoped to what slcan/evidence.py actually produces — see
docs/logging_and_evidence.md's "what this system deliberately does not do".
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

from rf_slcan import SlcanLibrary
from slcan import evidence as evidence_module
from slcan.exceptions import SlcanValidationError

_SCRIPTS_DIR = Path(__file__).parents[2] / "scripts"


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_evidence", _SCRIPTS_DIR / "validate_evidence.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_root(tmp_path) -> Path:
    session_root = tmp_path / "results" / "session" / "rf_slcan"
    run_dirs = sorted(session_root.iterdir())
    assert run_dirs, "no evidence run directory was created"
    return run_dirs[-1]


@pytest.fixture
def slcan_lib(tmp_path, monkeypatch):
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    lib = SlcanLibrary()
    lib._start_suite("EvidenceSuite", {})
    lib.connect(simulated=True, alias="default")
    lib.set_bitrate("500K")
    yield lib, tmp_path
    # best-effort teardown; individual tests may already have disconnected
    try:
        lib.disconnect()
    except Exception:  # noqa: BLE001, S110 - already-disconnected is the expected case here
        pass
    lib._end_suite("EvidenceSuite", {})


# ---------------------------------------------------------------------------
# Structure and manifest integrity
# ---------------------------------------------------------------------------

def test_end_suite_finalizes_a_complete_evidence_run(slcan_lib):
    lib, tmp_path = slcan_lib
    lib.open_channel("NORMAL")
    lib.send_frame(0x123, [0xAA, 0xBB, 0xCC])
    lib.close_channel()
    lib.disconnect()
    lib._end_suite("EvidenceSuite", {})

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
    assert summary["final_status"] == "PASS"
    assert summary["driver_id"] == "rf_slcan"
    assert summary["execution_mode"] == "SIMULATOR"  # connect(simulated=True) only


def test_manifest_hashes_match_files_on_disk(slcan_lib):
    lib, tmp_path = slcan_lib
    lib.open_channel("NORMAL")
    lib.close_channel()
    lib.disconnect()
    lib._end_suite("EvidenceSuite", {})
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


def test_manifest_lists_every_file_under_the_run_root(slcan_lib):
    lib, tmp_path = slcan_lib
    lib.disconnect()
    lib._end_suite("EvidenceSuite", {})
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
# Protocol trace content
# ---------------------------------------------------------------------------

def test_protocol_trace_captures_the_actual_slcan_wire_line(slcan_lib):
    lib, tmp_path = slcan_lib
    lib.open_channel("NORMAL")
    lib.send_frame(0x123, [0xAA, 0xBB, 0xCC])
    lib.close_channel()
    lib.disconnect()
    lib._end_suite("EvidenceSuite", {})
    root = _run_root(tmp_path)

    outbound = (root / "protocol" / "outbound_trace.log").read_text()
    assert "t1233AABBCC" in outbound  # standard frame, id=0x123, dlc=3, data=AABBCC
    assert "S6" in outbound  # bitrate 500K -> S-index 6
    assert "O" in outbound  # Open Channel NORMAL


# ---------------------------------------------------------------------------
# JSONL correctness: valid JSON, gap-free monotonic sequence per stream
# ---------------------------------------------------------------------------

def test_jsonl_streams_are_valid_and_gap_free(slcan_lib):
    lib, tmp_path = slcan_lib
    lib.open_channel("NORMAL")
    lib.send_frame(0x123, [0xAA])
    try:
        lib.close_channel(alias="unknown-alias")
    except Exception:  # noqa: BLE001, S110 - deliberately triggering a failed operation record
        pass
    lib.close_channel()
    lib.disconnect()
    lib._end_suite("EvidenceSuite", {})
    root = _run_root(tmp_path)

    for jsonl_path in root.rglob("*.jsonl"):
        sequences = []
        for line in jsonl_path.read_text().splitlines():
            record = json.loads(line)  # raises if not valid JSON
            sequences.append(record["sequence"])
        assert sequences == list(range(1, len(sequences) + 1)), jsonl_path


def test_nested_operations_share_one_correlation_id(slcan_lib):
    """Get Connection State(refresh=True) calls check_communication on the
    core driver, which itself is a _send_command; Connect's own operation
    record and its identify() protocol exchanges should correlate."""
    lib, tmp_path = slcan_lib
    lib.disconnect()
    lib._end_suite("EvidenceSuite", {})
    root = _run_root(tmp_path)
    operations = [json.loads(line) for line in (root / "events" / "operations.jsonl").read_text().splitlines()]
    connect_op = next(op for op in operations if op["capability"] == "Connect")
    set_bitrate_op = next(op for op in operations if op["capability"] == "Set Bitrate")
    assert connect_op["correlation_id"] != set_bitrate_op["correlation_id"]
    assert connect_op["operation_id"] != set_bitrate_op["operation_id"]

    exchanges = [json.loads(line) for line in (root / "protocol" / "exchanges.jsonl").read_text().splitlines()]
    connect_exchanges = [e for e in exchanges if e["operation_id"] == connect_op["operation_id"]]
    assert connect_exchanges, "Connect's own protocol exchanges (V/N queries) should be present"
    assert all(e["correlation_id"] == connect_op["correlation_id"] for e in connect_exchanges)


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------

def test_redact_mapping_masks_sensitive_keys():
    redacted = evidence_module.redact_mapping({"channel": 5, "password": "hunter2", "auth_token": "abc"})
    assert redacted["channel"] == 5
    assert redacted["password"] == {"value": "<REDACTED>", "redacted": True, "reason": "credential"}
    assert redacted["auth_token"]["redacted"] is True


def test_redaction_applies_to_operation_arguments(tmp_path, monkeypatch):
    """No current keyword takes a credential-shaped argument; this proves the
    plumbing redacts one anyway by exercising EvidenceRun.record_operation() directly."""
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    run = evidence_module.EvidenceRun(driver_id="rf_slcan", activity="session")
    with run.record_operation("Test Capability", arguments={"channel": 5, "api_token": "s3cr3t"}) as op:
        op.set_result("ok")
    run.finalize(status="PASS")

    operations = [json.loads(line) for line in (run.root / "events" / "operations.jsonl").read_text().splitlines()]
    record = operations[0]
    assert record["arguments"]["channel"] == 5
    assert record["arguments"]["api_token"] == {"value": "<REDACTED>", "redacted": True, "reason": "credential"}


# ---------------------------------------------------------------------------
# Execution mode honesty
# ---------------------------------------------------------------------------

def test_execution_mode_mixed_when_simulated_and_real_both_seen(tmp_path, monkeypatch):
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    run = evidence_module.EvidenceRun(driver_id="rf_slcan", activity="session")
    run.mark_execution_mode("SIMULATOR")
    assert run.execution_mode == "SIMULATOR"
    run.mark_execution_mode("REAL_HARDWARE")
    assert run.execution_mode == "MIXED"
    run.finalize(status="PASS")


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

def test_error_is_recorded_for_a_failed_operation(slcan_lib):
    lib, tmp_path = slcan_lib
    with pytest.raises(SlcanValidationError):
        lib.set_bitrate("not-a-bitrate")
    lib.disconnect()
    lib._end_suite("EvidenceSuite", {})
    root = _run_root(tmp_path)
    errors = [json.loads(line) for line in (root / "events" / "errors.jsonl").read_text().splitlines()]
    assert len(errors) == 1
    assert errors[0]["category"] == "VALIDATION"
    assert errors[0]["capability"] == "Set Bitrate"

    summary = json.loads((root / "run_summary.json").read_text())
    assert summary["error_count"] == 1
    assert summary["final_status"] == "PASS"  # disconnect/end_suite themselves still succeeded


# ---------------------------------------------------------------------------
# NullEvidenceRun / evidence_enabled=False
# ---------------------------------------------------------------------------

def test_evidence_disabled_writes_nothing_to_disk(tmp_path, monkeypatch):
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    lib = SlcanLibrary(evidence_enabled=False)
    lib._start_suite("Suite", {})
    lib.connect(simulated=True)
    lib.set_bitrate("500K")
    lib.disconnect()
    lib._end_suite("Suite", {})
    assert not (tmp_path / "results").exists()


def test_evidence_disabled_export_diagnostic_bundle_returns_none(tmp_path, monkeypatch):
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    lib = SlcanLibrary(evidence_enabled=False)
    lib.connect(simulated=True)
    assert lib.export_diagnostic_bundle() is None
    lib.disconnect()
    lib._end_suite("Suite", {})


# ---------------------------------------------------------------------------
# Export Diagnostic Bundle
# ---------------------------------------------------------------------------

def test_export_diagnostic_bundle_produces_a_readable_zip(slcan_lib):
    lib, _tmp_path = slcan_lib
    bundle_path = lib.export_diagnostic_bundle()
    assert bundle_path is not None
    archive_path = Path(bundle_path)
    assert archive_path.exists()
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        assert any(name.endswith("environment.json") for name in names)
        assert any(name.endswith("events/operations.jsonl") for name in names)


def test_export_diagnostic_bundle_honors_explicit_destination(slcan_lib):
    lib, tmp_path = slcan_lib
    destination = tmp_path / "custom" / "bundle.zip"
    result = lib.export_diagnostic_bundle(str(destination))
    assert Path(result) == destination
    assert destination.exists()


# ---------------------------------------------------------------------------
# validate_evidence.py
# ---------------------------------------------------------------------------

def test_validate_evidence_script_accepts_a_clean_run(slcan_lib):
    lib, tmp_path = slcan_lib
    lib.disconnect()
    lib._end_suite("EvidenceSuite", {})
    root = _run_root(tmp_path)
    validator = _load_validator()
    assert validator.validate(root) == []


def test_validate_evidence_script_detects_tampering(slcan_lib):
    lib, tmp_path = slcan_lib
    lib.disconnect()
    lib._end_suite("EvidenceSuite", {})
    root = _run_root(tmp_path)
    events_path = root / "events" / "events.jsonl"
    with events_path.open("a") as handle:
        handle.write("this is not json\n")
    validator = _load_validator()
    findings = validator.validate(root)
    assert any("HASH MISMATCH" in finding and "events.jsonl" in finding for finding in findings)
    assert any("invalid JSON" in finding for finding in findings)


def test_validate_evidence_script_detects_missing_manifest_entry(slcan_lib):
    lib, tmp_path = slcan_lib
    lib.disconnect()
    lib._end_suite("EvidenceSuite", {})
    root = _run_root(tmp_path)
    (root / "attachments" / "extra_note.txt").write_text("not tracked")
    validator = _load_validator()
    findings = validator.validate(root)
    assert any("FILE NOT IN MANIFEST" in finding for finding in findings)
