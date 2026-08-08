"""RFDS-008 evidence engine tests (§37: schema/correlation/ordering/redaction/integrity).

Scoped to what rf_bk8500b's evidence.py actually produces, in two layers:

- Direct tests of ``bk8500b.evidence`` (EvidenceRun, EvidenceAuditSink,
  EvidenceMetricsSink, TracingTransport) against a fake transport/device —
  no real hardware needed, exercises the genuinely new protocol-tracing code.
- Tests of ``BK8500BLibrary``'s keyword-level operation recording via its
  existing custom-``_device_factory`` test pattern (see ``tests/fakes.py``
  and ``tests/test_robot_library.py``).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest

from bk8500b import BK8500B, DriverConfig
from bk8500b import evidence as evidence_module
from BK8500BLibrary import BK8500BLibrary, BK8500BRobotError
from tests.fakes import FakeSCPITransport

_SCRIPTS_DIR = Path(__file__).parents[2] / "scripts"


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_evidence", _SCRIPTS_DIR / "validate_evidence.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_root(tmp_path: Path) -> Path:
    session_root = tmp_path / "results" / "session" / "rf_bk8500b"
    run_dirs = sorted(session_root.iterdir())
    assert run_dirs, "no evidence run directory was created"
    return run_dirs[-1]


# ---------------------------------------------------------------------------
# EvidenceRun / TracingTransport / EvidenceAuditSink, exercised directly
# against a fake transport (no real hardware, no Robot Framework)
# ---------------------------------------------------------------------------

def _make_traced_device(run: evidence_module.EvidenceRun) -> BK8500B:
    config = DriverConfig(port="FAKE", minimum_command_interval_s=0)
    fake_transport = FakeSCPITransport()
    traced = evidence_module.TracingTransport(fake_transport, run, session_alias="dut")
    audit_sink = evidence_module.EvidenceAuditSink(run, session_alias="dut")
    metrics_sink = evidence_module.EvidenceMetricsSink(run, session_alias="dut")
    return BK8500B(config, transport=traced, audit_sink=audit_sink, metrics_sink=metrics_sink)


def test_tracing_transport_records_outbound_and_inbound_protocol_exchanges(tmp_path, monkeypatch):
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    run = evidence_module.EvidenceRun(driver_id="rf_bk8500b", activity="session")
    device = _make_traced_device(run)
    device.connect()
    device.measure_voltage()
    run.finalize(status="PASS")

    outbound = (run.root / "protocol" / "outbound_trace.log").read_text()
    inbound = (run.root / "protocol" / "inbound_trace.log").read_text()
    assert "write" in outbound
    assert "read" in inbound
    exchanges = [json.loads(line) for line in (run.root / "protocol" / "exchanges.jsonl").read_text().splitlines()]
    assert any(entry["direction"] == "outbound" for entry in exchanges)
    assert any(entry["direction"] == "inbound" for entry in exchanges)


def test_audit_events_are_forwarded_into_evidence_events(tmp_path, monkeypatch):
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    run = evidence_module.EvidenceRun(driver_id="rf_bk8500b", activity="session")
    device = _make_traced_device(run)
    device.connect()
    run.finalize(status="PASS")

    events = [json.loads(line) for line in (run.root / "events" / "events.jsonl").read_text().splitlines()]
    audit_events = [event for event in events if event["event_type"].startswith("AUDIT_")]
    assert audit_events, "no AuditEvent was forwarded into the evidence stream"
    assert all("audit_event_id" in event["data"] for event in audit_events)


# ---------------------------------------------------------------------------
# Structure and manifest integrity
# ---------------------------------------------------------------------------

def test_manifest_hashes_match_files_on_disk(tmp_path, monkeypatch):
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    run = evidence_module.EvidenceRun(driver_id="rf_bk8500b", activity="session")
    device = _make_traced_device(run)
    device.connect()
    device.close()
    run.finalize(status="PASS")
    root = run.root

    manifest = json.loads((root / "evidence_manifest.json").read_text())
    assert manifest["artifact_count"] == len(manifest["artifacts"]) > 0
    for entry in manifest["artifacts"]:
        data = (root / entry["path"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry["sha256"]
        assert len(data) == entry["size_bytes"]
    listed = {entry["path"] for entry in manifest["artifacts"]}
    assert "evidence_manifest.json" not in listed
    assert "integrity/checksums.sha256" not in listed


def test_manifest_lists_every_file_under_the_run_root(tmp_path, monkeypatch):
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    run = evidence_module.EvidenceRun(driver_id="rf_bk8500b", activity="session")
    run.finalize(status="PASS")
    root = run.root
    manifest = json.loads((root / "evidence_manifest.json").read_text())
    listed = {entry["path"] for entry in manifest["artifacts"]}
    on_disk = {
        str(p.relative_to(root)).replace("\\", "/")
        for p in root.rglob("*")
        if p.is_file() and p.name not in ("evidence_manifest.json", "checksums.sha256")
    }
    assert listed == on_disk


def test_jsonl_streams_are_valid_and_gap_free(tmp_path, monkeypatch):
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    run = evidence_module.EvidenceRun(driver_id="rf_bk8500b", activity="session")
    device = _make_traced_device(run)
    device.connect()
    device.measure_voltage()
    device.measure_current()
    device.close()
    run.finalize(status="PASS")

    for jsonl_path in run.root.rglob("*.jsonl"):
        sequences = [json.loads(line)["sequence"] for line in jsonl_path.read_text().splitlines()]
        assert sequences == list(range(1, len(sequences) + 1)), jsonl_path


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------

def test_redact_mapping_masks_sensitive_keys():
    redacted = evidence_module.redact_mapping({"port": "FAKE", "password": "hunter2", "auth_token": "abc"})
    assert redacted["port"] == "FAKE"
    assert redacted["password"] == {"value": "<REDACTED>", "redacted": True, "reason": "credential"}
    assert redacted["auth_token"]["redacted"] is True


def test_redaction_applies_to_operation_arguments(tmp_path, monkeypatch):
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    run = evidence_module.EvidenceRun(driver_id="rf_bk8500b", activity="session")
    with run.record_operation("Test Capability", arguments={"port": "FAKE", "api_token": "s3cr3t"}) as op:
        op.set_result("ok")
    run.finalize(status="PASS")
    operations = [json.loads(line) for line in (run.root / "events" / "operations.jsonl").read_text().splitlines()]
    record = operations[0]
    assert record["arguments"]["port"] == "FAKE"
    assert record["arguments"]["api_token"] == {"value": "<REDACTED>", "redacted": True, "reason": "credential"}


# ---------------------------------------------------------------------------
# BK8500BLibrary keyword-level operation recording (custom device_factory,
# matching this project's own existing fake-transport test pattern)
# ---------------------------------------------------------------------------

def _library_with_fake_factory(**kwargs) -> BK8500BLibrary:
    library = BK8500BLibrary(**kwargs)

    def factory(config):
        return BK8500B(replace(config, minimum_command_interval_s=0), transport=FakeSCPITransport())

    library._device_factory = factory
    return library


def test_keyword_operations_are_recorded_even_with_a_custom_device_factory(tmp_path, monkeypatch):
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    library = _library_with_fake_factory()
    library.connect_to_electronic_load("FAKE")
    library.measure_voltage()
    library.disconnect_all_electronic_loads()

    root = _run_root(tmp_path)
    operations = [json.loads(line) for line in (root / "events" / "operations.jsonl").read_text().splitlines()]
    capabilities = {op["capability"] for op in operations}
    assert "Connect To Electronic Load" in capabilities
    assert "Measure Voltage" in capabilities
    assert "Disconnect All Electronic Loads" in capabilities

    summary = json.loads((root / "run_summary.json").read_text())
    assert summary["final_status"] == "PASS"


def test_error_is_recorded_on_keyword_failure(tmp_path, monkeypatch):
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    library = _library_with_fake_factory()
    with pytest.raises(BK8500BRobotError):
        library.measure_voltage()  # no session connected yet
    library.connect_to_electronic_load("FAKE")
    library.disconnect_all_electronic_loads()

    root = _run_root(tmp_path)
    errors = [json.loads(line) for line in (root / "events" / "errors.jsonl").read_text().splitlines()]
    assert len(errors) == 1
    assert errors[0]["capability"] == "Measure Voltage"


# ---------------------------------------------------------------------------
# evidence_enabled=False
# ---------------------------------------------------------------------------

def test_evidence_disabled_writes_nothing_to_disk(tmp_path, monkeypatch):
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    library = _library_with_fake_factory(evidence_enabled=False)
    library.connect_to_electronic_load("FAKE")
    library.measure_voltage()
    library.disconnect_all_electronic_loads()
    assert not (tmp_path / "results").exists()


def test_evidence_disabled_export_diagnostic_bundle_returns_none(tmp_path, monkeypatch):
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    library = _library_with_fake_factory(evidence_enabled=False)
    assert library.export_diagnostic_bundle() is None


# ---------------------------------------------------------------------------
# Export Diagnostic Bundle
# ---------------------------------------------------------------------------

def test_export_diagnostic_bundle_produces_a_readable_zip(tmp_path, monkeypatch):
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    library = _library_with_fake_factory()
    library.connect_to_electronic_load("FAKE")
    bundle_path = library.export_diagnostic_bundle()
    assert bundle_path is not None
    with zipfile.ZipFile(bundle_path) as archive:
        names = archive.namelist()
        assert any(name.endswith("environment.json") for name in names)
        assert any(name.endswith("events/operations.jsonl") for name in names)
    library.disconnect_all_electronic_loads()


# ---------------------------------------------------------------------------
# validate_evidence.py
# ---------------------------------------------------------------------------

def test_validate_evidence_script_accepts_a_clean_run(tmp_path, monkeypatch):
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    library = _library_with_fake_factory()
    library.connect_to_electronic_load("FAKE")
    library.disconnect_all_electronic_loads()
    root = _run_root(tmp_path)
    validator = _load_validator()
    assert validator.validate(root) == []


def test_validate_evidence_script_detects_tampering(tmp_path, monkeypatch):
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    library = _library_with_fake_factory()
    library.connect_to_electronic_load("FAKE")
    library.disconnect_all_electronic_loads()
    root = _run_root(tmp_path)
    with (root / "events" / "events.jsonl").open("a") as handle:
        handle.write("this is not json\n")
    validator = _load_validator()
    findings = validator.validate(root)
    assert any("HASH MISMATCH" in finding and "events.jsonl" in finding for finding in findings)
    assert any("invalid JSON" in finding for finding in findings)
