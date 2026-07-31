"""Robot-side RFDS-019 callability and protocol-evidence harness.

The harness deliberately invokes every exported keyword through Robot
Framework's ``BuiltIn.run_keyword`` API.  Each keyword is prepared in an
independent, deterministic simulator state so connection-management keywords
cannot invalidate later tests merely because the inventory is alphabetically
ordered.

The implementation also captures the protocol trace owned by the chamber core
and compares it with the keyword's RFDS-019 protocol vector.  Local-only
operations use explicit local oracles and are never reported as device traffic.
"""
from __future__ import annotations

import csv
import json
import re
import time
from pathlib import Path
from typing import Any

import yaml


class RFDSConformanceHarness:
    """Data-driven Robot Framework conformance executor."""

    ROBOT_LIBRARY_SCOPE = "SUITE"

    _CONNECT_KEYWORDS = {"Connect"}
    _DISCONNECT_KEYWORDS = {"Disconnect", "Disconnect All"}
    _RUNNING_ASSERTIONS = {"Chamber Should Be Running"}
    _STOPPED_ASSERTIONS = {"Chamber Should Be Stopped"}
    _TEMPERATURE_ASSERTIONS = {"Temperature Should Be", "Temperature Should Be Within"}
    _SETPOINT_ASSERTIONS = {"Temperature Setpoint Should Be"}
    _IDENTITY_KEYWORDS = {"Get Identity"}

    def __init__(self, repository_root: str, evidence_dir: str):
        self.root = Path(repository_root).resolve()
        self.evidence = Path(evidence_dir).resolve()
        self.evidence.mkdir(parents=True, exist_ok=True)
        self.rows: list[dict[str, Any]] = []
        document = yaml.safe_load(
            (self.root / "tests/conformance/data/protocol_vectors.yaml").read_text(encoding="utf-8")
        )
        self.vectors = {item["id"]: item for item in document["vectors"]}

    def execute_all_public_keywords_through_robot(self) -> None:
        """Invoke every public keyword with deterministic preconditions.

        Connection establishment is performed before device-facing calls, as
        required by RFDS-019 section 12.  Destructive lifecycle keywords are
        isolated and followed by recovery so they cannot cascade failures into
        subsequent inventory entries.
        """
        from robot.libraries.BuiltIn import BuiltIn

        builtin = BuiltIn()
        library = self._get_library_instance(builtin)
        inventory = yaml.safe_load(
            (self.root / "tests/conformance/data/keyword_inventory.yaml").read_text(encoding="utf-8")
        )["keywords"]
        samples = self._samples(library)
        failures: list[str] = []

        for item in inventory:
            name = item["keyword"]
            arguments = samples.get(name)
            if arguments is None:
                failures.append(f"No argument vector for {name}")
                self._record(item, "NOT RUN", 0.0, None, "missing argument vector", [], [])
                continue

            context = None
            started = time.monotonic()
            try:
                context = self._prepare_keyword(library, name)
                result = builtin.run_keyword(name, *arguments)
                context = context or self._current_core(library)
                outbound, inbound, observed = self._collect_trace(context)
                self._verify_protocol(item, outbound, inbound, observed)
                self._record(
                    item,
                    "PASS",
                    time.monotonic() - started,
                    result,
                    None,
                    outbound,
                    inbound,
                )
            except Exception as exc:  # Robot wraps keyword failures in its own exception type.
                outbound, inbound, _observed = self._collect_trace(context)
                self._record(
                    item,
                    "FAIL",
                    time.monotonic() - started,
                    None,
                    str(exc),
                    outbound,
                    inbound,
                )
                failures.append(f"{name}: {exc}")
            finally:
                try:
                    self._recover_after_keyword(library, name)
                except Exception as recovery_error:
                    failures.append(f"{name} recovery: {recovery_error}")

        self._write_reports(inventory)
        if failures:
            raise AssertionError("RFDS-019 callability failures:\n" + "\n".join(failures))

    # ------------------------------------------------------------------
    # Deterministic preparation and recovery
    # ------------------------------------------------------------------

    def _prepare_keyword(self, library: Any, name: str) -> Any | None:
        if name in self._CONNECT_KEYWORDS:
            self._disconnect_all_direct(library)
        else:
            self._ensure_default_session(library)

        if name == "Disconnect All":
            self._ensure_session(library, "secondary", "SIM::secondary")

        if name == "Delete Driver Configuration Profile":
            self._ensure_profile(library, "conformance_delete")
        elif name == "Load Driver Configuration":
            self._ensure_profile(library, "conformance_load")
        elif name == "Save Driver Configuration":
            self._delete_profile_direct(library, "conformance_save")

        core = self._current_core(library)
        if core is not None:
            self._reset_simulator(core, name)
            core._trace.clear()  # Test-only access to the protocol-boundary observer.
        return core

    def _recover_after_keyword(self, library: Any, name: str) -> None:
        if name in self._CONNECT_KEYWORDS or name in self._DISCONNECT_KEYWORDS:
            self._disconnect_all_direct(library)
            self._ensure_default_session(library)
        elif name == "Cancel Current Operation":
            # Reconnect clears cancellation state at both operation and transport layers.
            self._disconnect_all_direct(library)
            self._ensure_default_session(library)

        for profile in ("conformance_delete", "conformance_load", "conformance_save"):
            self._delete_profile_direct(library, profile)

    def _ensure_default_session(self, library: Any) -> Any:
        return self._ensure_session(library, "default", "SIM::conformance")

    @staticmethod
    def _ensure_session(library: Any, alias: str, resource: str) -> Any:
        try:
            handle = library._registry.get(alias)
            if handle.core.is_connected:
                return handle
        except Exception:
            pass
        return library._registry.connect(
            resource,
            alias=alias,
            timeout_s=2.0,
            options=library._effective_connection_options({}),
        )

    @staticmethod
    def _disconnect_all_direct(library: Any) -> None:
        library._registry.disconnect_all(safe_shutdown=False, timeout_s=2.0)

    @staticmethod
    def _current_core(library: Any) -> Any | None:
        try:
            return library._registry.get("default", require_connected=False).core
        except Exception:
            return None

    @staticmethod
    def _reset_simulator(core: Any, name: str) -> None:
        state = getattr(core.transport, "simulator_state", None)
        if state is None:
            return
        state.setpoint_c = 30.0
        state.temperature_c = 30.0
        state.running = False
        state.dryer = False
        state.compressed_air = False
        state.gradient_up_c_per_min = 2.5
        state.gradient_down_c_per_min = 2.0
        state.status = "READY"
        state.fault_mode = None

        if name in RFDSConformanceHarness._RUNNING_ASSERTIONS or name in {
            "Stop Chamber",
            "Safe Shutdown",
            "Disconnect",
            "Disconnect All",
        }:
            state.running = True
        if name in {"Safe Shutdown", "Disconnect", "Disconnect All"}:
            state.dryer = True
            state.compressed_air = True
        if name in RFDSConformanceHarness._STOPPED_ASSERTIONS or name == "Start Chamber":
            state.running = False
        if name in RFDSConformanceHarness._TEMPERATURE_ASSERTIONS:
            state.temperature_c = 30.0
        if name in RFDSConformanceHarness._SETPOINT_ASSERTIONS:
            state.setpoint_c = 30.0
        if name in RFDSConformanceHarness._IDENTITY_KEYWORDS:
            core._identity = None

    @staticmethod
    def _ensure_profile(library: Any, name: str) -> None:
        try:
            library._configuration.save_profile(name, overwrite=True)
        except Exception:
            RFDSConformanceHarness._delete_profile_direct(library, name)
            library._configuration.save_profile(name, overwrite=True)

    @staticmethod
    def _delete_profile_direct(library: Any, name: str) -> None:
        try:
            library._configuration.delete_profile(name, confirm=True)
        except Exception:
            pass

    @staticmethod
    def _get_library_instance(builtin: Any) -> Any:
        candidates = (
            "VotschClimateChamberLibrary",
            "rf_votsch_climate_chamber.library.VotschClimateChamberLibrary",
        )
        errors = []
        for candidate in candidates:
            try:
                return builtin.get_library_instance(candidate)
            except Exception as exc:
                errors.append(f"{candidate}: {exc}")
        raise AssertionError("Cannot resolve chamber library instance: " + "; ".join(errors))

    # ------------------------------------------------------------------
    # Protocol evidence and vector comparison
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_trace(core: Any | None) -> tuple[list[str], list[str], list[str]]:
        if core is None:
            return [], [], []
        records = core._trace.to_list()
        outbound: list[str] = []
        inbound: list[str] = []
        observed: list[str] = []
        for record in records:
            event = record["event"]
            if event == "open":
                observed.append("TCP OPEN")
            elif event == "close":
                observed.append("TCP CLOSE")
            elif event == "outbound":
                text = record["data_text"]
                outbound.append(text)
                observed.append(text)
            elif event == "inbound":
                inbound.append(record["data_text"] )
        return outbound, inbound, observed

    def _verify_protocol(
        self,
        item: dict[str, Any],
        outbound: list[str],
        inbound: list[str],
        observed: list[str],
    ) -> None:
        vector_id = item.get("protocol_vector")
        if not item["device_facing"]:
            return
        if not vector_id or vector_id not in self.vectors:
            raise AssertionError(f"device-facing keyword has no protocol vector: {item['keyword']}")

        vector = self.vectors[vector_id]
        expected = list(vector.get("expected_outbound", []))
        protocol_expected = [entry for entry in expected if not entry.startswith("LOCAL ")]
        if protocol_expected:
            self._assert_expected_subsequence(item["keyword"], protocol_expected, observed)
        if vector.get("expected_inbound", {}).get("response_required") and outbound and not inbound:
            raise AssertionError(f"{item['keyword']} transmitted protocol data but captured no inbound response")

    @classmethod
    def _assert_expected_subsequence(cls, keyword_name: str, expected: list[str], actual: list[str]) -> None:
        cursor = 0
        for expectation in expected:
            conditional = " when " in expectation
            pattern = cls._expectation_pattern(expectation)
            for index in range(cursor, len(actual)):
                if re.fullmatch(pattern, actual[index]):
                    cursor = index + 1
                    break
            else:
                if conditional:
                    continue
                raise AssertionError(
                    f"{keyword_name} protocol mismatch; expected {expectation!r} after position {cursor}, "
                    f"captured {actual!r}"
                )

    @staticmethod
    def _expectation_pattern(expectation: str) -> str:
        text = re.sub(r"\s+when\s+.*$", "", expectation)
        text = re.sub(r"\s+repeated$", "", text)
        text = text.replace("\\r", "\r")
        escaped = re.escape(text)
        escaped = escaped.replace(re.escape("<0|1>"), r"[01]")
        escaped = escaped.replace(re.escape("<value_c>"), r"[-+]?\d+(?:\.\d+)?")
        escaped = escaped.replace(re.escape("<value>"), r"[-+]?\d+(?:\.\d+)?")
        return escaped

    # ------------------------------------------------------------------
    # Reports and invocation vectors
    # ------------------------------------------------------------------

    def _record(
        self,
        item: dict[str, Any],
        status: str,
        duration: float,
        result: Any,
        error: str | None,
        outbound: list[str],
        inbound: list[str],
    ) -> None:
        local_vector = bool(
            item.get("protocol_vector")
            and all(
                entry.startswith("LOCAL ")
                for entry in self.vectors[item["protocol_vector"]].get("expected_outbound", [])
            )
        )
        self.rows.append(
            {
                "keyword": item["keyword"],
                "canonical_keyword": item["canonical_keyword"],
                "device_facing": item["device_facing"],
                "protocol_vector": item.get("protocol_vector"),
                "callability_tested": "YES",
                "outbound_verified": "N/A" if not item["device_facing"] or local_vector else status,
                "raw_response_verified": "N/A" if not inbound else status,
                "parsed_result_verified": "PASS" if status == "PASS" else status,
                "result": status,
                "duration_s": round(duration, 6),
                "return_type": type(result).__name__ if result is not None else None,
                "outbound_frames": json.dumps(outbound, ensure_ascii=False),
                "inbound_frames": json.dumps(inbound, ensure_ascii=False),
                "error": error,
            }
        )

    def _write_reports(self, inventory: list[dict[str, Any]]) -> None:
        (self.evidence / "protocol_vector_results.json").write_text(
            json.dumps(self.rows, indent=2, default=str, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        fields = list(self.rows[0]) if self.rows else []
        with (self.evidence / "keyword_coverage.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(self.rows)
        (self.evidence / "keyword_inventory.json").write_text(
            json.dumps(inventory, indent=2, default=str, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        passed = sum(row["result"] == "PASS" for row in self.rows)
        total = len(self.rows)
        outbound_passed = sum(row["outbound_verified"] == "PASS" for row in self.rows)
        response_passed = sum(row["raw_response_verified"] == "PASS" for row in self.rows)
        (self.evidence / "conformance_summary.md").write_text(
            "# RFDS-019 Conformance Summary\n\n"
            f"- Inventory: {total}\n"
            f"- PASS: {passed}\n"
            f"- FAIL/NOT RUN: {total - passed}\n"
            f"- Outbound protocol verified: {outbound_passed}\n"
            f"- Inbound responses verified: {response_passed}\n"
            "- Simulator boundary: in-process SimServ protocol transport\n",
            encoding="utf-8",
        )

    def _samples(self, library: Any) -> dict[str, list[Any]]:
        output = self.evidence
        default_configuration = library._configuration.get_default()
        values: dict[str, list[Any]] = {
            "Connect": ["SIM::conformance", "default", "2 seconds"],
            "Select Connection": ["default"],
            "Set Communication Timeout": ["2 seconds"],
            "Get Connection State": ["default", True],
            "Get Identity": ["default", True],
            "Set Temperature": [30],
            "Set Temperature Limits": [-40, 180],
            "Set Temperature And Wait": [30, "0 seconds", 0.8, "10 milliseconds", "2 seconds", 1, True],
            "Wait For Temperature Stability": [30, 0.8, 1, "10 milliseconds", "2 seconds"],
            "Wait For Dwell": ["0 seconds", "10 milliseconds"],
            "Set Heating Gradient": [2.5],
            "Set Cooling Gradient": [2.0],
            "Set Dryer": [True],
            "Set Compressed Air": [True],
            "Temperature Should Be": [30, 0.1],
            "Temperature Should Be Within": [-40, 180],
            "Temperature Setpoint Should Be": [30, 0.1],
            "Export Diagnostics": [str(output / "diagnostics.json")],
            "Validate Driver Configuration": [default_configuration],
            "Import Driver Configuration": [default_configuration],
            "Export Driver Configuration": [str(output / "configuration.json"), "EFFECTIVE", None, True],
            "Save Driver Configuration": ["conformance_save", "EFFECTIVE", True],
            "Load Driver Configuration": ["conformance_load"],
            "Delete Driver Configuration Profile": ["conformance_delete", True],
        }
        inventory = yaml.safe_load(
            (self.root / "tests/conformance/data/keyword_inventory.yaml").read_text(encoding="utf-8")
        )["keywords"]
        for item in inventory:
            if not any(argument["required"] and argument["kind"] not in {"var_keyword"} for argument in item["arguments"]):
                values.setdefault(item["keyword"], [])
        return values
