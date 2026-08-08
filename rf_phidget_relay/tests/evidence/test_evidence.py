"""RFDS-008 evidence engine tests (§37: schema/correlation/ordering/redaction/integrity).

Scoped to what rf_phidget_relay's evidence.py actually produces — this is not
an attempt to cover every optional item in the RFDS-008 checklist, see
docs/logging_and_evidence.md's "what this system deliberately does not do".
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

from rf_phidget_relay import PhidgetRelayLibrary
from rf_phidget_relay import evidence as evidence_module

_SCRIPTS_DIR = Path(__file__).parents[2] / "scripts"


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_evidence", _SCRIPTS_DIR / "validate_evidence.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeOutput:
    def __init__(self):
        self.serial = None
        self.channel = None
        self.state = False

    def setDeviceSerialNumber(self, value):
        self.serial = value

    def setChannel(self, value):
        self.channel = value

    def openWaitForAttachment(self, _timeout):
        pass

    def setState(self, value):
        self.state = bool(value)

    def getState(self):
        return self.state

    def close(self):
        pass


def _run_root(tmp_path) -> Path:
    session_root = tmp_path / "results" / "session" / "rf_phidget_relay"
    run_dirs = sorted(session_root.iterdir())
    assert run_dirs, "no evidence run directory was created"
    return run_dirs[-1]


@pytest.fixture
def relay(tmp_path, monkeypatch):
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    obj = PhidgetRelayLibrary(output_factory=FakeOutput, sleep_function=lambda _s: None)
    obj.connect_relays(111111, 222222)
    yield obj, tmp_path


# ---------------------------------------------------------------------------
# Structure and manifest integrity
# ---------------------------------------------------------------------------

def test_disconnect_finalizes_a_complete_evidence_run(relay):
    obj, tmp_path = relay
    obj.close_relay(5)
    obj.disconnect_relays()
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
    assert summary["driver_id"] == "rf_phidget_relay"
    assert summary["execution_mode"] == "FAKE"  # output_factory was explicitly supplied


def test_manifest_hashes_match_files_on_disk(relay):
    obj, tmp_path = relay
    obj.close_relay(3)
    obj.disconnect_relays()
    root = _run_root(tmp_path)

    manifest = json.loads((root / "evidence_manifest.json").read_text())
    assert manifest["artifact_count"] == len(manifest["artifacts"])
    assert manifest["artifact_count"] > 0
    for entry in manifest["artifacts"]:
        artifact_path = root / entry["path"]
        data = artifact_path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry["sha256"]
        assert len(data) == entry["size_bytes"]

    # evidence_manifest.json and checksums.sha256 are self-referential and are
    # deliberately excluded from their own listing (see evidence.py _write_manifest).
    listed_paths = {entry["path"] for entry in manifest["artifacts"]}
    assert "evidence_manifest.json" not in listed_paths
    assert "integrity/checksums.sha256" not in listed_paths


def test_manifest_lists_every_file_under_the_run_root(relay):
    obj, tmp_path = relay
    obj.disconnect_relays()
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
# JSONL correctness: valid JSON, gap-free monotonic sequence per stream
# ---------------------------------------------------------------------------

def test_jsonl_streams_are_valid_and_gap_free(relay):
    obj, tmp_path = relay
    obj.close_relay(1)
    obj.get_all_relay_states()
    try:
        obj.close_relay(99)
    except Exception:
        pass
    obj.disconnect_relays()
    root = _run_root(tmp_path)

    for jsonl_path in root.rglob("*.jsonl"):
        sequences = []
        for line in jsonl_path.read_text().splitlines():
            record = json.loads(line)  # raises if not valid JSON
            sequences.append(record["sequence"])
        assert sequences == list(range(1, len(sequences) + 1)), jsonl_path


def test_nested_operations_share_one_correlation_id(relay):
    """Close Relay calls Set Relay State internally; both should correlate."""
    obj, tmp_path = relay
    obj.close_relay(2)
    obj.disconnect_relays()
    root = _run_root(tmp_path)
    operations = [json.loads(line) for line in (root / "events" / "operations.jsonl").read_text().splitlines()]
    close_relay_op = next(op for op in operations if op["capability"] == "Close Relay")
    set_state_op = next(
        op
        for op in operations
        if op["capability"] == "Set Relay State" and op["arguments"].get("channel") == 2
    )
    assert close_relay_op["correlation_id"] == set_state_op["correlation_id"]
    assert close_relay_op["operation_id"] != set_state_op["operation_id"]


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
    plumbing redacts one anyway if a future keyword or caller passes one, by
    exercising EvidenceRun.record_operation() directly."""
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    run = evidence_module.EvidenceRun(driver_id="rf_phidget_relay", activity="session")
    with run.record_operation("Test Capability", arguments={"channel": 5, "api_token": "s3cr3t"}) as op:
        op.set_result("ok")
    run.finalize(status="PASS")

    operations = [json.loads(line) for line in (run.root / "events" / "operations.jsonl").read_text().splitlines()]
    record = operations[0]
    assert record["arguments"]["channel"] == 5
    assert record["arguments"]["api_token"] == {"value": "<REDACTED>", "redacted": True, "reason": "credential"}


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

def test_error_is_recorded_once_per_failed_operation(relay):
    obj, tmp_path = relay
    with pytest.raises(Exception):
        obj.close_relay(99)
    obj.disconnect_relays()
    root = _run_root(tmp_path)
    errors = [json.loads(line) for line in (root / "events" / "errors.jsonl").read_text().splitlines()]
    # close_relay(99) fails validation inside the nested Set Relay State call
    # AND inside Close Relay itself re-raising it: two distinct operation
    # failures, so two distinct error records is correct (not double-counted
    # bookkeeping — see run_summary error_count assertion below).
    assert len(errors) == 2
    assert {error["category"] for error in errors} == {"VALIDATION"}

    summary = json.loads((root / "run_summary.json").read_text())
    assert summary["error_count"] == 2
    assert summary["final_status"] == "PASS"  # disconnect itself succeeded


# ---------------------------------------------------------------------------
# NullEvidenceRun / evidence_enabled=False
# ---------------------------------------------------------------------------

def test_evidence_disabled_writes_nothing_to_disk(tmp_path, monkeypatch):
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    obj = PhidgetRelayLibrary(output_factory=FakeOutput, evidence_enabled=False, sleep_function=lambda _s: None)
    obj.connect_relays(111111, 222222)
    obj.close_relay(4)
    obj.disconnect_relays()
    assert not (tmp_path / "results").exists()


def test_evidence_disabled_export_diagnostic_bundle_returns_none(tmp_path, monkeypatch):
    monkeypatch.setenv("RFDS_EVIDENCE_ROOT", str(tmp_path / "results"))
    obj = PhidgetRelayLibrary(output_factory=FakeOutput, evidence_enabled=False)
    obj.connect_relays(111111, 222222)
    assert obj.export_diagnostic_bundle() is None
    obj.disconnect_relays()


# ---------------------------------------------------------------------------
# Export Diagnostic Bundle
# ---------------------------------------------------------------------------

def test_export_diagnostic_bundle_produces_a_readable_zip(relay):
    obj, tmp_path = relay
    obj.close_relay(6)
    bundle_path = obj.export_diagnostic_bundle()
    assert bundle_path is not None
    archive_path = Path(bundle_path)
    assert archive_path.exists()

    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        assert any(name.endswith("environment.json") for name in names)
        assert any(name.endswith("events/operations.jsonl") for name in names)
    obj.disconnect_relays()


def test_export_diagnostic_bundle_honors_explicit_destination(relay):
    obj, tmp_path = relay
    destination = tmp_path / "custom" / "bundle.zip"
    result = obj.export_diagnostic_bundle(str(destination))
    assert Path(result) == destination
    assert destination.exists()
    obj.disconnect_relays()


# ---------------------------------------------------------------------------
# validate_evidence.py
# ---------------------------------------------------------------------------

def test_validate_evidence_script_accepts_a_clean_run(relay):
    obj, tmp_path = relay
    obj.close_relay(7)
    obj.disconnect_relays()
    root = _run_root(tmp_path)
    validator = _load_validator()
    findings = validator.validate(root)
    assert findings == []


def test_validate_evidence_script_detects_tampering(relay):
    obj, tmp_path = relay
    obj.disconnect_relays()
    root = _run_root(tmp_path)
    events_path = root / "events" / "events.jsonl"
    with events_path.open("a") as handle:
        handle.write("this is not json\n")
    validator = _load_validator()
    findings = validator.validate(root)
    assert any("HASH MISMATCH" in finding and "events.jsonl" in finding for finding in findings)
    assert any("invalid JSON" in finding for finding in findings)


def test_validate_evidence_script_detects_missing_manifest_entry(relay):
    obj, tmp_path = relay
    obj.disconnect_relays()
    root = _run_root(tmp_path)
    (root / "attachments" / "extra_note.txt").write_text("not tracked")
    validator = _load_validator()
    findings = validator.validate(root)
    assert any("FILE NOT IN MANIFEST" in finding for finding in findings)
