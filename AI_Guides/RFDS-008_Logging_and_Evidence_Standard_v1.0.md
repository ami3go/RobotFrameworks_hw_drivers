# RFDS-008 — Logging and Evidence Standard

## Standard Evidence, Robot Framework Reports, JSON, JSONL, CSV, Traces, and Diagnostic Bundles

**Document ID:** RFDS-008  
**Version:** 1.0  
**Status:** Draft Project Standard (Normative)  
**Applies to:** All RFDS Robot Framework driver packages, shared platform components, protocol simulators, test suites, hardware-in-the-loop benches, generic GUIs, examples, review workflows, CI pipelines, and release packages

---

## 1. Purpose

This specification defines the mandatory logging, evidence, traceability, and result-export requirements for the RFDS Robot Framework Driver Platform.

It establishes one consistent evidence model so that a developer, tester, reviewer, CI system, operator, or AI agent can determine:

1. what software and configuration were used;
2. what driver, device, fixture, simulator, or bench was addressed;
3. what operation or Robot Framework keyword was executed;
4. what arguments and preconditions applied;
5. what protocol operation was transmitted when applicable;
6. what raw response, measurement, state, or error was observed;
7. how the result was interpreted;
8. whether cleanup and safe-state actions succeeded;
9. which requirement, test, protocol vector, review finding, or release the evidence supports;
10. whether the evidence is complete, authentic, internally consistent, and tied to the exact tested revision.

RFDS-008 defines the **project-wide evidence schema and preservation rules**. It does not replace Robot Framework reporting, RFDS-009 testing requirements, RFDS-019 call and protocol conformance, RFDS-010 review requirements, or RFDS-011 release evidence. It standardizes how those activities record and exchange evidence.

---

## 2. Goals

The RFDS logging and evidence system shall:

- produce human-readable and machine-readable records from the same execution;
- preserve authoritative raw evidence separately from derived summaries and visualizations;
- provide deterministic correlation from a Robot Framework test to driver operations, protocol traces, device responses, measurements, errors, cleanup, reviews, and releases;
- make missing, incomplete, skipped, excluded, simulated, or physically unverified evidence explicit;
- support offline review without requiring access to the original test computer;
- preserve enough environment and identity information to reproduce or explain a result;
- protect credentials, private keys, tokens, sensitive connection data, and private bench information;
- prevent later report generation or formatting from silently changing authoritative results;
- support long-duration, high-sample-rate, and multi-driver tests without losing sequence or source identity;
- provide integrity records suitable for release review and later audit.

---

## 3. Scope Boundary

### 3.1 In scope

RFDS-008 covers:

- Python and driver operational logs;
- Robot Framework `output.xml`, `log.html`, and `report.html`;
- optional Robot Framework xUnit output;
- test-run, suite, test, keyword, operation, measurement, error, safety, cleanup, and protocol evidence;
- JSON documents and JSON Lines event streams;
- canonical CSV measurement and coverage exports;
- timestamps, sequencing, run identifiers, correlation identifiers, and source identifiers;
- environment, dependency, configuration, driver, device, simulator, fixture, and bench identity;
- simulator-versus-real-hardware declaration;
- raw-versus-derived evidence classification;
- protocol trace references required by RFDS-019;
- HIL evidence required by RFDS-009 and RFDS-018;
- GUI and manual-operation evidence required by RFDS-012;
- configuration fingerprints and migration evidence required by RFDS-014;
- release and review evidence integration;
- evidence manifests, checksums, completeness status, redaction, retention, and diagnostic-bundle export;
- evidence validation tests and release acceptance criteria.

### 3.2 Out of scope

RFDS-008 does not define:

- the complete public Robot Framework keyword API;
- vendor-specific protocol syntax;
- transport implementation;
- the exception hierarchy and error taxonomy owned by RFDS-007;
- which tests must exist or which physical properties must be verified;
- device-specific acceptance limits;
- measurement uncertainty calculation for a specific laboratory process;
- calibration laboratory accreditation;
- cryptographic signing infrastructure not available to the project;
- organisation-wide legal retention periods;
- cloud storage, database, log aggregation, or telemetry vendor selection;
- a mandatory charting or GUI toolkit;
- a replacement for source control, issue tracking, or release management.

Where another RFDS specification defines stricter evidence requirements for its scope, the stricter requirements shall apply.

---

## 4. Normative References

A conforming implementation shall apply the relevant approved revisions of:

- **RFDS-001 — Platform Requirements**;
- **RFDS-002 — Mandatory Public API and Robot Framework Keyword Standard**;
- **RFDS-003 — BaseInstrumentLibrary**;
- **RFDS-004 — Transport Layer Specification**;
- **RFDS-005 — Driver Package Specification**;
- **RFDS-006 — Coding Standard**;
- **RFDS-007 — Error and Exception Standard**;
- **RFDS-009 — Testing Standard**;
- **RFDS-010 — Driver Review Checklist**;
- **RFDS-011 — Release Process**;
- **RFDS-012 — GUI Integration Specification**;
- **RFDS-013 — Capability Model**;
- **RFDS-014 — Driver Configuration Model Specification**;
- **RFDS-015 — Plugin Architecture**;
- **RFDS-017 — AI Driver Contract Specification**;
- **RFDS-018 — AI Test Bench Contract Specification**;
- **RFDS-019 — Robot Framework Driver Call and Protocol Conformance Test Specification**;
- **RFDS-020 — Driver Implementation Lifecycle**;
- the device-specific implementation requirements;
- applicable vendor documentation and approved bench procedures.

When requirements conflict, precedence shall be:

1. safety and legal requirements;
2. approved bench and device constraints;
3. authoritative raw evidence;
4. the latest approved specialised RFDS requirement;
5. derived summaries, presentations, or convenience exports.

A conflict shall not be silently reconciled. It shall be recorded as an evidence inconsistency and reviewed.

---

## 5. Normative Terminology

- **shall / shall not** — mandatory requirement;
- **should / should not** — recommended requirement; deviation requires documented justification;
- **may** — permitted implementation choice;
- **run** — one bounded execution producing one evidence root;
- **run ID** — globally unique identifier for one execution;
- **correlation ID** — identifier relating events belonging to one logical operation or workflow;
- **operation ID** — identifier for one invocation of a public capability, driver method, transport action, GUI request, or equivalent action;
- **sequence number** — monotonically increasing integer used to preserve event order within a defined stream;
- **authoritative evidence** — the primary record from which a result is determined;
- **derived evidence** — a report, graph, summary, converted file, or calculation generated from authoritative evidence;
- **raw evidence** — bytes, text, samples, responses, traces, or state captured before semantic conversion where practical;
- **evidence manifest** — machine-readable inventory of evidence files, roles, hashes, sizes, and completeness;
- **diagnostic bundle** — sanitized export containing the records needed to investigate a run or operational failure;
- **evidence producer** — component that creates an evidence record;
- **evidence consumer** — person or tool that reads, validates, summarizes, or audits evidence;
- **real-hardware evidence** — evidence obtained from an identified physical device or fixture;
- **simulation evidence** — evidence obtained from an approved simulator, fake, replay, or mock boundary;
- **redaction** — removal or irreversible replacement of sensitive values while retaining evidence structure;
- **evidence completeness** — declared status indicating whether all required artifacts were successfully finalized.

---

## 6. Core Evidence Principles

### 6.1 No silent success

A component shall not record success when a required operation, response, assertion, cleanup, evidence write, or finalization step failed.

### 6.2 No silent evidence loss

Dropped events, missing samples, failed flushes, truncated files, unavailable attachments, or post-processing failures shall be visible in the run summary and evidence manifest.

### 6.3 Raw evidence preservation

When a decision depends on protocol data, measurement samples, device responses, screenshots, waveforms, or other raw observations, the authoritative raw evidence shall be preserved or its approved external location and integrity reference shall be recorded.

### 6.4 Derived evidence traceability

Every derived report, graph, table, or summary shall identify its source evidence files and generation method or tool version.

### 6.5 Exact-revision binding

Evidence used for gate, review, qualification, or release approval shall identify the exact source revision, package version, built artifact, and checksum when available.

Evidence from another revision shall not be reused as proof without an explicit compatibility justification approved by review authority.

### 6.6 Simulation honesty

Simulation, replay, mock, and real-hardware evidence shall be clearly distinguishable. Simulation evidence shall not be represented as proof of physical accuracy, calibration, wiring, electrical behaviour, or hardware safety.

### 6.7 Finite finalization

Evidence writers shall use finite timeouts and shall not block test or application shutdown indefinitely.

### 6.8 Append-only event history

Operational event streams should be append-only during execution. Existing finalized records shall not be rewritten without creating a new revision and recording the transformation.

### 6.9 Evidence before convenience

Lossless machine-readable evidence takes precedence over human-friendly layout. HTML, PDF, images, and dashboards shall not replace required JSON, JSONL, CSV, XML, or raw traces.

### 6.10 Stable schemas

Machine-readable evidence shall declare a schema name and schema version. Breaking schema changes require a new major schema version and migration or compatibility documentation.

---

## 7. Evidence Classification

Each artifact shall declare one of the following roles:

| Role | Meaning | Examples |
|---|---|---|
| `AUTHORITATIVE_RESULT` | Primary result authority | Robot `output.xml`, validated result JSON |
| `RAW_OBSERVATION` | Unprocessed or minimally framed observation | protocol trace, waveform binary, device response capture |
| `STRUCTURED_EVENT` | Append-only machine-readable event | `events.jsonl`, `errors.jsonl` |
| `STRUCTURED_MEASUREMENT` | Machine-readable measurement data | canonical long-form CSV, measurement JSONL |
| `IDENTITY` | Environment, software, hardware, fixture, or contract identity | `environment.json`, `device_identity.json` |
| `CONFIGURATION` | Effective or selected configuration evidence | redacted configuration, fingerprint, migration report |
| `DERIVED_REPORT` | Human-readable or summarized output | `log.html`, `report.html`, Markdown summary, PDF report |
| `VISUALIZATION` | Plot, image, screenshot, or rendered diagram | PNG, SVG, PDF graph |
| `INTEGRITY` | Hash, manifest, provenance, or signature information | `evidence_manifest.json`, checksum files |
| `REVIEW` | Review findings, disposition, or approval | review Markdown, JSON finding list |
| `RELEASE` | Release-specific evidence | release manifest, SBOM, provenance |

An artifact may have one primary role and additional tags, but it shall not be ambiguously presented as both raw and derived.

---

## 8. Evidence Levels

The following levels describe increasing evidence scope. A project may produce several levels in one run.

### 8.1 E0 — Operational Diagnostics

Minimum evidence for application or driver operation outside a formal test:

- run/session identity;
- software and driver versions;
- effective mode and profile;
- operation events;
- errors and recovery;
- cleanup and final state;
- redaction status.

### 8.2 E1 — Robot Framework Test Evidence

E0 plus:

- Robot `output.xml`;
- Robot `log.html`;
- Robot `report.html`;
- suite/test identifiers;
- test result totals;
- test variables or a redacted effective-variable record;
- setup and teardown result evidence.

### 8.3 E2 — Structured Measurement Evidence

E1 plus:

- canonical measurement data in CSV or JSONL;
- measurement metadata and units;
- limits and result classification;
- source instrument and channel;
- sample sequencing and timestamps;
- raw-versus-calculated classification;
- data-loss and validity flags.

### 8.4 E3 — Protocol and Conformance Evidence

E1 plus applicable E2 evidence and:

- RFDS-019 keyword inventory and protocol vectors;
- outbound protocol trace;
- inbound response trace;
- parsed-result evidence;
- error and recovery vectors;
- protocol coverage matrix.

### 8.5 E4 — Release and Qualification Evidence

All applicable lower-level evidence plus:

- exact release candidate identity and checksums;
- clean-build and clean-install environment;
- test-layer summary and coverage;
- HIL identity and qualification status;
- review records and finding disposition;
- release manifest, SBOM, provenance, and evidence-manifest integrity.

A release shall state the highest evidence level actually achieved. It shall not imply a higher level from the presence of selected files alone.

---

## 9. Canonical Run Identity

### 9.1 Run ID

Every execution shall have one unique `run_id` generated before the first operational event.

Recommended format:

```text
run-<UTC basic timestamp>-<random or UUID suffix>
```

Example:

```text
run-20260727T081530.412Z-7f3a21c8
```

### 9.2 Required identifiers

As applicable, evidence shall use:

- `run_id` — complete execution;
- `suite_id` — one Robot suite;
- `test_id` — one Robot test;
- `keyword_id` — one Robot keyword execution when captured;
- `correlation_id` — one logical workflow or request;
- `operation_id` — one driver or capability invocation;
- `protocol_exchange_id` — one protocol command/query/response exchange;
- `sample_id` — one measurement sample;
- `attachment_id` — one attachment;
- `finding_id` — one review finding;
- `requirement_id` — one requirement reference;
- `protocol_vector_id` — one RFDS-019 vector;
- `session_alias` — one driver connection/session.

### 9.3 Identifier stability

Identifiers shall remain stable across all artifacts from the same run. Derived reports shall reuse the source identifiers rather than inventing unrelated identifiers.

### 9.4 Multi-process and multi-driver runs

When several processes or drivers contribute evidence, each producer shall also record:

- `producer_id`;
- process ID where useful;
- host ID or sanitized host name;
- driver/plugin ID;
- session alias;
- local event sequence.

A merge process shall preserve original producer and sequence information.

---

## 10. Time and Ordering

### 10.1 Wall-clock timestamps

Machine-readable evidence shall use RFC 3339 / ISO 8601 timestamps with timezone.

UTC is required for stored evidence unless an approved local-time field is additionally provided.

Example:

```text
2026-07-27T08:15:30.412Z
```

### 10.2 Sub-second precision

Timestamps should preserve millisecond precision at minimum. Higher precision may be used when meaningful and supported by the platform.

### 10.3 Monotonic time

Durations, deadlines, and ordering of events within one process shall use a monotonic clock where available.

Evidence should include:

- `timestamp_utc`;
- `monotonic_ns` or equivalent;
- `duration_s` for completed operations.

### 10.4 Clock status

A run shall record whether wall-clock synchronization was known, unknown, or failed. Multi-host tests should record clock source or observed offset when time alignment matters.

### 10.5 Sequence numbers

Every JSONL event stream shall include a monotonically increasing `sequence` per producer. Duplicate or missing sequence numbers shall be detected during evidence validation.

---

## 11. Canonical Result Directory

Each execution shall write to a dedicated result directory. Runtime results shall not be mixed with source-controlled package content.

Recommended layout:

```text
results/<activity>/<driver_or_bench>/<timestamp>_<run_id>/
├── evidence_manifest.json
├── run_summary.json
├── run_summary.md
├── environment.json
├── software_inventory.json
├── driver_inventory.json
├── device_identity.json
├── bench_identity.json
├── configuration/
│   ├── effective_configuration.redacted.json
│   ├── configuration_fingerprint.json
│   └── migration_report.json
├── robot/
│   ├── output.xml
│   ├── log.html
│   ├── report.html
│   └── xunit.xml
├── events/
│   ├── events.jsonl
│   ├── operations.jsonl
│   ├── errors.jsonl
│   ├── safety.jsonl
│   └── resource_locks.jsonl
├── measurements/
│   ├── measurements.csv
│   ├── measurements_metadata.json
│   └── domain_specific/
├── protocol/
│   ├── outbound_trace.log
│   ├── inbound_trace.log
│   ├── exchanges.jsonl
│   └── attachments/
├── coverage/
│   ├── keyword_coverage.csv
│   ├── requirement_coverage.csv
│   └── code_coverage/
├── attachments/
│   ├── screenshots/
│   ├── waveforms/
│   ├── plots/
│   └── other/
├── cleanup/
│   ├── cleanup_summary.json
│   └── final_state.json
└── integrity/
    ├── checksums.sha256
    └── provenance.json
```

Only applicable files are mandatory. `run_summary.json` and `evidence_manifest.json` shall state why expected files are absent.

### 11.1 Atomic result-root allocation

The result directory shall be created before test execution and shall not overwrite a previous run. If a collision occurs, execution shall create a different run ID or fail visibly.

### 11.2 Temporary files

In-progress files should use a temporary suffix and be atomically renamed when finalized. Abandoned temporary files shall be listed as incomplete evidence.

---

## 12. Mandatory Run Summary

Every run shall produce `run_summary.json`.

It shall contain at least:

- schema name and version;
- run ID;
- activity type;
- start and end timestamps;
- total duration;
- execution mode: `SIMULATOR`, `REPLAY`, `FAKE`, `REAL_HARDWARE`, `MIXED`, or `NO_HARDWARE`;
- driver, package, and platform versions;
- source revision and release-candidate checksum where applicable;
- selected profile;
- suite/test totals where applicable;
- final run status;
- evidence completeness status;
- safe-start and safe-teardown status where applicable;
- count of errors, warnings, dropped events, dropped samples, retries, and incomplete artifacts;
- device and bench identity references;
- Robot artifact references;
- measurement and protocol artifact references;
- exclusions, skips, deviations, and limitations;
- evidence-manifest reference;
- redaction status;
- generation tool and schema version.

The Markdown summary shall be derived from `run_summary.json` and other declared source artifacts.

---

## 13. Result and Evidence Statuses

### 13.1 Test and verification statuses

Where applicable, the standard statuses are:

- `PASS` — all required oracles passed;
- `FAIL` — one or more required oracles failed;
- `ERROR` — execution infrastructure or unexpected failure prevented a valid result;
- `SKIP` — declared prerequisite unavailable or approved conditional test not executed;
- `EXCLUDED` — intentionally not applicable or prohibited with approved reason;
- `ABORTED` — execution was stopped before completion;
- `NOT_RUN` — no execution occurred;
- `UNKNOWN` — state cannot be determined from available evidence.

Specialised specifications may permit a subset. Their stricter rules take precedence.

### 13.2 Evidence completeness statuses

- `COMPLETE` — all required artifacts finalized and validated;
- `COMPLETE_WITH_DECLARED_OMISSIONS` — omitted artifacts are permitted and explained;
- `INCOMPLETE` — one or more required artifacts are missing, truncated, invalid, or not finalized;
- `CORRUPT` — evidence integrity or schema validation failed;
- `UNVERIFIED` — evidence exists but integrity validation was not executed.

A test result may be `PASS` while evidence completeness is `INCOMPLETE`; such a run shall not satisfy release acceptance when complete evidence is required.

---

## 14. Robot Framework Evidence

### 14.1 Mandatory Robot artifacts

Every formal Robot Framework test run shall produce:

- `output.xml`;
- `log.html`;
- `report.html`.

`output.xml` is the authoritative Robot Framework result artifact. HTML files are derived presentations.

### 14.2 File placement

Robot artifacts shall be stored under the run-specific `robot/` directory or an equivalent path referenced by the evidence manifest.

### 14.3 Naming

Standard filenames should be retained. When multiple Robot invocations occur in one run, each invocation shall use a unique subdirectory or filename prefix and shall be listed in the manifest.

### 14.4 xUnit

CI workflows should generate `xunit.xml` when supported. xUnit output shall not replace Robot `output.xml`.

### 14.5 Listener integration

RFDS drivers and platform components should provide or use a Robot listener or equivalent integration that records:

- suite and test IDs;
- keyword start and end;
- public keyword name;
- session alias;
- operation and correlation IDs;
- result status and duration;
- evidence references;
- setup and teardown results.

The listener shall not expose secrets or duplicate very large payloads already stored as attachments.

### 14.6 Robot log levels

The following mapping should be used consistently:

| RFDS intent | Robot/Python level |
|---|---|
| Detailed internal diagnostic | `DEBUG` |
| Normal lifecycle and meaningful operation | `INFO` |
| Recoverable or non-blocking concern | `WARN` |
| Test- or operation-affecting failure | `ERROR` or Robot failure |
| Trace-level protocol bytes | dedicated trace artifact or `TRACE` where available |

Protocol traces shall not be embedded only in HTML logs when machine-readable or raw trace evidence is required.

### 14.7 Embedded attachments

Robot logs may link to screenshots, plots, CSV files, traces, or other attachments. The underlying files shall remain independently accessible in the result directory.

### 14.8 Rebot and merged outputs

When Robot outputs are merged or post-processed with Rebot:

- original `output.xml` files shall be preserved;
- merged output shall be marked as derived;
- the Rebot version and command shall be recorded;
- test identities shall remain traceable to source outputs.

---

## 15. Structured Event Logging

### 15.1 JSON Lines format

Append-only operational streams shall use UTF-8 JSON Lines (`.jsonl`) unless an equivalent approved format is required.

Each line shall contain exactly one JSON object and end with `\n`.

### 15.2 Common event envelope

Every structured event shall contain at least:

```json
{
  "schema": "rfds.event",
  "schema_version": "1.0.0",
  "run_id": "run-20260727T081530.412Z-7f3a21c8",
  "producer_id": "rf_keysight_n6700:PSU_MAIN",
  "sequence": 124,
  "timestamp_utc": "2026-07-27T08:15:31.004Z",
  "monotonic_ns": 5830123491234,
  "level": "INFO",
  "event_type": "OPERATION_COMPLETED",
  "correlation_id": "corr-000045",
  "operation_id": "op-000092",
  "source": {
    "component": "driver",
    "driver_id": "keysight_n6700",
    "session_alias": "PSU_MAIN"
  },
  "message": "Set DC voltage completed",
  "data": {},
  "evidence_refs": []
}
```

### 15.3 Required event types

The implementation shall record applicable events for:

- process or application start and stop;
- package and driver loading;
- contract, manifest, capability, and configuration validation;
- connection attempts and results;
- device identity;
- session creation, selection, and closure;
- public keyword or capability request;
- argument validation;
- operation start and completion;
- transport write, query, read, timeout, disconnect, and recovery at an appropriate evidence level;
- state transitions;
- resource-lock acquisition, contention, and release;
- retries and retry decisions;
- device errors and driver exceptions;
- operator confirmations and actions;
- stop, abort, emergency, and cleanup;
- measurement acquisition and data loss;
- configuration import, comparison, migration, apply, rollback, save, and export;
- Robot suite and run lifecycle;
- evidence finalization and integrity validation.

### 15.4 Arguments and results

Arguments and results shall be represented using JSON-compatible values. Large binary data, waveforms, screenshots, or long text shall be stored as attachments and referenced.

### 15.5 Sensitive values

Sensitive fields shall be redacted before serialization. Redaction shall occur at the producer boundary where practical, not only during later bundle export.

---

## 16. Operation Evidence

Every state-changing or device-facing public operation shall have an operation record containing, as applicable:

- operation ID and correlation ID;
- originating Robot suite/test/keyword, GUI action, Python call, or automation;
- driver and session alias;
- capability ID and public keyword;
- canonical keyword and alias used;
- start and end timestamps;
- validated arguments with secrets redacted;
- precondition status;
- execution mode and selected profile;
- resource locks;
- timeout, retry policy, and actual retries;
- whether transmission occurred;
- protocol exchange references;
- raw and parsed response references;
- return value or result schema;
- state before and after when relevant;
- error and recovery references;
- cleanup requirement and cleanup result;
- final status.

A successful operation record shall not omit a required protocol or measurement reference merely because the operation returned without an exception.

---

## 17. Error and Exception Evidence

### 17.1 Required error fields

Every recorded error shall contain, as applicable:

- error ID;
- timestamp and sequence;
- run, correlation, operation, session, suite, test, and keyword IDs;
- RFDS error category and code defined by RFDS-007;
- exception type;
- concise message;
- causal chain;
- component and source location;
- whether transmission occurred;
- device state or uncertainty;
- recoverability classification;
- retry attempted and result;
- recovery action and result;
- cleanup and safe-state result;
- evidence references;
- operator guidance;
- redacted traceback for diagnostics.

### 17.2 Tracebacks

Tracebacks shall be retained for internal or unexpected failures. Expected validation errors may omit a full traceback when the structured cause is sufficient.

### 17.3 Preserving the original failure

A cleanup or recovery failure shall not overwrite the original error. Both shall be recorded and linked.

### 17.4 Error deduplication

Repeated identical errors may be summarized for presentation, but the authoritative event stream shall preserve occurrence count, first and last timestamps, affected operations, and any state changes.

---

## 18. Environment and Software Evidence

Every formal run shall record, as applicable:

- operating system, version, and architecture;
- host identifier or sanitized host name;
- Python executable and version;
- virtual environment identity;
- Robot Framework version;
- RFDS platform/core version;
- driver distribution and library versions;
- package build version and source revision;
- installed dependency names and versions relevant to the run;
- vendor runtime and backend versions;
- transport backend version;
- locale, timezone, and decimal conventions when relevant;
- process command line with secrets redacted;
- CI workflow, job, runner, and commit identity;
- container or virtual-machine identity when used;
- clock synchronization status;
- evidence schema versions.

The complete installed package inventory may be stored as a separate file. The run summary shall reference it.

---

## 19. Driver, Device, Simulator, Fixture, and Bench Identity

### 19.1 Driver identity

Record:

- RFDS driver ID;
- plugin ID where applicable;
- distribution name;
- public library name;
- package and library version;
- supported-device family;
- capability-model version and hash;
- RFDS-017 contract version and lock/hash;
- configuration schema version;
- RFDS-019 vector-set version or hash where applicable.

### 19.2 Real-device identity

Record when available:

- manufacturer;
- model;
- serial number;
- firmware version;
- hardware revision;
- installed modules, cards, options, or channel count;
- transport type and sanitized resource address;
- identity query and raw response reference;
- calibration status when material to the test;
- selected channel or subdevice mapping.

### 19.3 Simulator and replay identity

Record:

- simulator/replay name and version;
- protocol boundary implemented;
- scenario or replay-set identifier;
- deterministic seed where applicable;
- source capture or vector-set hash;
- known limitations;
- whether real-device behaviour is emulated, replayed, or authored.

### 19.4 Fixture and reference equipment

Record when applicable:

- fixture identifier and revision;
- relay or switching map;
- reference instruments and serial numbers;
- calibration status relevant to the result;
- cable, probe, adapter, or load identifiers when required by the bench procedure;
- RFDS-018 bench contract version and hash.

### 19.5 Sensitive device identity

Where device serial numbers, addresses, or topology are considered sensitive, policy may tokenize or redact them. The evidence shall state that redaction occurred and preserve stable non-secret correlation tokens.

---

## 20. Configuration Evidence

Each run shall record the effective configuration used, with secrets redacted.

Required configuration evidence includes, as applicable:

- configuration schema name and version;
- selected profile name;
- profile source and fingerprint;
- effective configuration fingerprint;
- value-source provenance where supported;
- environment-variable overrides with values redacted where sensitive;
- session overrides;
- safety limits and authorization flags;
- validation result;
- migration history;
- imported profile hash;
- applied-versus-persisted distinction;
- device-persistent writes;
- rollback result;
- unknown or ignored fields;
- redaction status.

Configuration fingerprints shall exclude or normalize secret values according to RFDS-014 while remaining useful for comparing effective non-secret configuration.

---

## 21. Measurement Evidence

### 21.1 Canonical long-form schema

The canonical tabular measurement export shall be long-form: one row per observed or calculated quantity per sample.

Mandatory columns are:

```text
schema_version
run_id
suite_id
test_id
correlation_id
operation_id
sample_id
sequence
timestamp_utc
elapsed_s
source_driver_id
session_alias
device_id
channel
quantity
value
unit
value_kind
validity
status
```

Additional standard columns should include when applicable:

```text
requested_value
requested_unit
readback_value
readback_unit
lower_limit
upper_limit
limit_unit
error_value
error_unit
error_percent
uncertainty
uncertainty_unit
range
mode
resolution
sample_period_s
stabilization_s
raw_reference
calculation_id
notes
```

### 21.2 Value kind

`value_kind` shall use one of:

- `REQUESTED`;
- `SETPOINT`;
- `READBACK`;
- `MEASURED`;
- `CALCULATED`;
- `ESTIMATED`;
- `DERIVED_LIMIT`;
- `STATUS_VALUE`.

Requested, actual, read-back, measured, and calculated values shall not be silently conflated.

### 21.3 Validity

`validity` shall use one of:

- `VALID`;
- `INVALID`;
- `STALE`;
- `OVER_RANGE`;
- `UNDER_RANGE`;
- `NOT_SETTLED`;
- `DROPPED`;
- `UNKNOWN`.

### 21.4 Numeric representation

Finite numeric values shall be written as decimal numbers using `.` as the decimal separator. Locale-specific decimal commas shall not be used in canonical CSV or JSON.

`NaN`, positive infinity, and negative infinity shall not be emitted as non-standard JSON numbers. They shall use a nullable value plus explicit validity/status fields.

### 21.5 Precision

Stored values shall preserve available source precision without inventing additional accuracy. Presentation formatting may reduce displayed precision but shall not change authoritative numeric data.

### 21.6 Units

Units shall be explicit and should use stable SI or domain-standard symbols. A value without a unit is permitted only for dimensionless quantities, counts, enumerations, or explicitly unitless device results.

### 21.7 Limits and pass/fail

When a measurement is judged against limits, evidence shall record:

- lower and upper limits as applicable;
- inclusive or exclusive boundary semantics;
- unit;
- comparison method;
- tolerance or uncertainty treatment;
- resulting status;
- requirement or oracle reference.

### 21.8 Streaming data

Streaming evidence shall preserve:

- sample sequence;
- acquisition timestamp;
- configured sample period;
- actual elapsed time;
- dropped or late sample count;
- buffering or down-sampling;
- source channel;
- raw data reference when display data are down-sampled.

### 21.9 Calculated values

Calculated values shall record a calculation identifier or method version and references to source sample IDs or source files.

---

## 22. CSV Requirements

### 22.1 Encoding and dialect

Canonical CSV files shall use:

- UTF-8 encoding without requiring a byte-order mark;
- comma delimiter;
- double-quote text qualifier;
- CRLF or LF line endings, consistently within a file;
- RFC 4180-compatible escaping;
- one header row;
- stable column names;
- `.` decimal separator;
- ISO 8601 timestamps with timezone.

### 22.2 Missing values

Missing values shall be empty fields unless the schema defines a specific token. `UNKNOWN`, `NOT_APPLICABLE`, and invalid numeric states shall use dedicated status fields rather than ambiguous text in numeric columns.

### 22.3 Column order

Canonical schemas shall define a stable column order. Additional extension columns may be appended after standard columns and shall use a driver- or domain-qualified prefix when collision is possible.

### 22.4 Metadata sidecar

Each canonical CSV should have a JSON metadata sidecar containing:

- schema and version;
- file role;
- run ID;
- generation timestamp;
- producer and version;
- row count;
- column definitions and units;
- source evidence references;
- hash;
- dropped-row or truncation status.

### 22.5 Wide-form exports

Domain-specific wide-form CSV files may be generated for convenience. They shall be marked as derived unless they preserve the complete canonical dataset and metadata.

### 22.6 Spreadsheet safety

Text fields beginning with `=`, `+`, `-`, or `@` and intended for spreadsheet opening shall be escaped or represented safely to prevent formula injection. The chosen policy shall not alter authoritative protocol or measurement values.

### 22.7 Large files

Large CSV files may be split by size, time, channel, or suite. The manifest shall preserve ordering, partition criteria, and total row count.

---

## 23. JSON and JSONL Requirements

### 23.1 Encoding

JSON and JSONL shall use UTF-8.

### 23.2 Schema declaration

Every top-level JSON document and every JSONL record shall declare a schema name and version directly or through an unambiguous file-level contract.

### 23.3 JSON compatibility

Machine-readable records shall use standard JSON values only. Python objects, tuples, bytes, datetime objects, Decimal values, or enums shall be converted using documented lossless or explicit representations.

### 23.4 Field naming

Machine-readable field names shall use `snake_case` ASCII identifiers.

### 23.5 Unknown fields

Consumers shall follow the declared schema compatibility policy. Producers shall not silently remove unknown fields when round-trip preservation is required.

### 23.6 Large payloads

Large binary or repeated payloads shall be stored in attachments and referenced by path, media type, size, and hash.

### 23.7 JSONL recovery

A parser should be able to recover all complete lines before a truncated final line. Truncation shall mark the artifact incomplete.

---

## 24. Protocol and Transport Evidence

RFDS-019 is authoritative for public keyword call and protocol conformance. RFDS-008 defines the common evidence envelope and storage rules.

Protocol evidence shall record, as applicable:

- protocol exchange ID;
- operation ID, keyword, capability, and vector IDs;
- transport type;
- destination or resource token with sensitive parts redacted;
- direction: outbound or inbound;
- timestamp and sequence;
- exact bytes or text, or attachment reference;
- normalized representation used by the oracle;
- framing, terminator, address, channel, function, checksum, headers, or body fields;
- response-required declaration;
- timeout;
- transmission result;
- raw response;
- parse result;
- device error query or status;
- retry or recovery relation;
- oracle result.

### 24.1 Binary traces

Binary protocol data shall be preserved losslessly as binary attachments or encoded using a documented representation such as hexadecimal or Base64. Human-readable hexdumps are derived evidence unless byte-for-byte reconstruction is possible and validated.

### 24.2 Exact versus normalized traces

When comparison requires normalization, both raw and normalized forms shall be retained or the normalization method shall be documented and reproducible.

### 24.3 Trace volume

High-volume traces may use rotation, partitioning, compression, or selective capture. The policy shall be declared before execution and shall not omit evidence required by the test oracle.

### 24.4 Credentials

HTTP authorization headers, tokens, passwords, private keys, and secret query parameters shall be redacted before evidence persistence.

---

## 25. Safety, State, and Cleanup Evidence

For hardware-changing operations, evidence shall record:

- declared safe initial state;
- observed or queried initial state;
- uncertainty where physical state is not independently verified;
- safety limits and interlock status;
- authorization or operator confirmation;
- state-changing operations;
- stop, abort, and emergency requests;
- cleanup steps attempted;
- per-step cleanup result;
- final queried or measured state;
- safe-state confidence: `VERIFIED`, `COMMANDED_ONLY`, `UNKNOWN`, or `FAILED`;
- remaining hazards and required operator action.

A software command to enter safe state shall not be described as physically verified unless an appropriate oracle confirms it.

Teardown failure shall be visible in the Robot report, run summary, and cleanup summary.

---

## 26. Requirement and Traceability Evidence

### 26.1 Traceability links

Evidence shall support links among:

```text
requirement
    ↕
capability / public keyword
    ↕
implementation component
    ↕
test case / protocol vector
    ↕
execution result
    ↕
raw evidence
    ↕
review finding / release decision
```

### 26.2 Requirement coverage matrix

A generated requirement coverage matrix should contain:

- requirement ID;
- source document and version;
- applicability;
- implementation reference;
- capability or keyword reference;
- test ID;
- protocol vector where applicable;
- execution mode;
- result status;
- evidence references;
- review status;
- deviation or exclusion ID;
- notes.

### 26.3 No unsupported completion claims

A requirement shall not be marked `PASS` only because code exists or a test case is present. Executed evidence and applicable oracles are required.

---

## 27. Attachments and Visual Evidence

### 27.1 Supported attachments

Attachments may include:

- screenshots;
- plots;
- waveform files;
- logic-analyser captures;
- device configuration dumps;
- firmware logs;
- photos of fixture wiring;
- PDFs;
- binary protocol captures;
- exported instrument files;
- calibration certificates when permitted;
- operator notes.

### 27.2 Attachment metadata

Every attachment shall have metadata containing:

- attachment ID;
- file path;
- media type;
- role;
- size;
- hash;
- creation timestamp;
- producing component;
- related run, test, operation, sample, protocol exchange, or finding IDs;
- source device or instrument;
- raw or derived classification;
- redaction or transformation status;
- description.

### 27.3 Plots

Plots shall:

- label axes and units;
- identify series and source quantities;
- distinguish measured, requested, read-back, and calculated data;
- state filtering, smoothing, interpolation, averaging, or down-sampling;
- link to source data;
- avoid implying precision absent from source evidence.

### 27.4 Screenshots and photographs

Screenshots and photographs are supporting evidence. They shall not replace machine-readable state or measurement evidence when such evidence is available.

### 27.5 PDF reports

PDF reports are derived evidence. Their source JSON, CSV, Robot XML, and attachment references shall be retained.

---

## 28. Logging Levels and Content Policy

### 28.1 Levels

The standard levels are:

- `TRACE` — detailed protocol or internal sequence information;
- `DEBUG` — diagnostic implementation detail;
- `INFO` — normal lifecycle, identity, state, and operation information;
- `WARN` — recoverable anomaly, degradation, retry, incomplete optional evidence, or suspicious condition;
- `ERROR` — operation, test, evidence, recovery, cleanup, or system failure;
- `CRITICAL` — unsafe state, evidence corruption affecting release truth, emergency failure, or unrecoverable platform failure.

### 28.2 Message quality

Messages shall be concise, specific, actionable, and correlated. They should identify the affected driver/session/operation and avoid generic statements such as “something failed”.

### 28.3 Duplicate content

Large payloads shall not be repeated across Python logs, Robot logs, JSONL, and traces. Logs should reference the authoritative attachment.

### 28.4 Standard context

Log records should include automatically injected context:

- run ID;
- correlation ID;
- operation ID;
- driver ID;
- session alias;
- suite/test/keyword ID where available;
- source component.

### 28.5 Console versus file logs

Console logs may be concise. File and structured logs shall retain sufficient detail for diagnosis and audit.

---

## 29. Redaction, Privacy, and Security

### 29.1 Secrets prohibited in evidence

Evidence shall not contain plaintext:

- passwords;
- API tokens;
- private keys;
- client secrets;
- authentication cookies;
- bearer tokens;
- unredacted credential-bearing URLs;
- secret environment variables;
- private certificate material.

### 29.2 Sensitive fields

Potentially sensitive fields include:

- personal paths and user names;
- private IP addressing and topology;
- device serial numbers;
- operator names;
- customer or DUT identifiers;
- proprietary commands or captures;
- calibration certificates.

Project or deployment policy shall define whether these are retained, tokenized, or redacted.

### 29.3 Redaction markers

Redacted values shall use an explicit structure or marker, for example:

```json
{
  "value": "<REDACTED>",
  "redacted": true,
  "reason": "credential"
}
```

### 29.4 Stable tokens

When correlation is needed across runs, a sensitive identifier may be replaced with a stable project-controlled token. The token shall not permit practical recovery of the original value without separately protected information.

### 29.5 Redaction validation

Automated evidence validation shall scan for known secret patterns and configured sensitive fields. A detected secret is release-blocking until evidence is regenerated or securely sanitized.

### 29.6 Raw trace policy

Raw traces that inherently contain secrets shall be disabled, filtered, or stored under an approved restricted-access policy. They shall not be included in public release archives.

---

## 30. Integrity, Manifest, and Provenance

### 30.1 Evidence manifest

Every formal run shall produce `evidence_manifest.json` containing one entry per artifact.

Each entry shall include:

- relative path;
- artifact role;
- media type;
- schema name and version where applicable;
- size in bytes;
- SHA-256 hash;
- creation or finalization timestamp;
- producer and producer version;
- authoritative or derived classification;
- source artifact references for derived files;
- completeness status;
- redaction status;
- retention class;
- optional external-location reference.

### 30.2 Finalization order

The manifest shall be generated after all normal artifacts are finalized. The final manifest hash may be stored separately in `integrity/checksums.sha256` or release evidence.

### 30.3 Hash validation

Evidence validation shall recalculate hashes and report missing, modified, duplicate, or unexpected files.

### 30.4 Provenance

For release or qualification evidence, provenance shall identify:

- source revision;
- build command or workflow;
- build environment;
- package and release artifact hashes;
- test commands;
- evidence generation tools;
- post-processing steps;
- reviewer or approval record references.

### 30.5 Immutable reviewed evidence

Evidence used for final release approval shall be frozen. Any later modification requires a new manifest and review determination.

---

## 31. Evidence Completeness and Finalization

### 31.1 Finalization workflow

At run completion, the evidence subsystem shall:

1. stop accepting normal events;
2. flush buffers;
3. close and finalize stream files;
4. record dropped-event and dropped-sample counts;
5. finalize Robot outputs;
6. finalize attachments and sidecars;
7. calculate totals and status;
8. generate run summary;
9. generate evidence manifest and hashes;
10. validate schemas, references, row counts, sequences, and hashes;
11. mark the final completeness status.

### 31.2 Crash recovery

After an abnormal termination, a recovery tool should:

- locate abandoned run directories;
- preserve complete JSONL lines and valid files;
- mark truncated artifacts;
- generate a recovery summary without changing original content;
- set completeness to `INCOMPLETE` or `CORRUPT` as applicable.

### 31.3 Evidence writer failures

Evidence-writer failures shall be surfaced immediately when they can invalidate the run. A formal qualification run shall normally fail or be marked invalid when mandatory evidence cannot be written.

---

## 32. Retention, Compression, and Archiving

### 32.1 Retention class

Each run or artifact shall declare a retention class such as:

- `EPHEMERAL_DIAGNOSTIC`;
- `DEVELOPMENT`;
- `GATE_REVIEW`;
- `REGRESSION_BASELINE`;
- `HIL_QUALIFICATION`;
- `RELEASE`;
- `SECURITY_RESTRICTED`.

Actual retention periods are deployment policy, but release and qualification evidence shall not be treated as ephemeral.

### 32.2 Compression

Evidence may be compressed after finalization. Compression shall preserve filenames, relative paths, timestamps where practical, and hashes of uncompressed authoritative files or the complete archive.

### 32.3 Archive naming

Recommended diagnostic or evidence archive naming:

```text
rfds_evidence_<driver_or_bench>_<UTC timestamp>_<run_id>.zip
```

### 32.4 Deletion

Deletion of reviewed or release evidence shall require an approved retention action. Tools shall not silently delete previous run directories to make space.

### 32.5 Storage exhaustion

Low-space conditions shall be detected before long runs where practical. If storage exhaustion occurs, the run shall record evidence loss and shall not claim complete evidence.

---

## 33. Diagnostic Bundle

Each driver or RFDS application shall provide a repeatable way to export a diagnostic bundle containing applicable:

- run summary;
- evidence manifest;
- environment and software inventory;
- driver, device, simulator, fixture, and bench identity;
- sanitized effective configuration and fingerprints;
- operational events;
- errors and tracebacks;
- cleanup and final state;
- Robot artifacts;
- relevant protocol traces;
- measurements and attachments needed for diagnosis;
- redaction report;
- known limitations.

The bundle shall exclude secrets and unrelated historical data. The export command and redaction policy shall be documented.

---

## 34. Performance and Reliability

### 34.1 Non-blocking behaviour

Normal logging shall not introduce unbounded blocking into driver operations. Buffered or asynchronous logging may be used when ordering and flush semantics remain deterministic.

### 34.2 Backpressure

When evidence production exceeds storage throughput, the system shall use a declared policy:

- block within a finite bound;
- buffer within a declared limit;
- down-sample only non-authoritative presentation data;
- drop lower-priority diagnostics with explicit counters;
- fail the run when mandatory evidence cannot be preserved.

### 34.3 Rotation

Long-duration logs may rotate by size or time. Rotated files shall retain sequence continuity and manifest entries.

### 34.4 Resource limits

Evidence generation should have defined limits for:

- queue depth;
- maximum attachment size;
- maximum in-memory buffer;
- file rotation size;
- flush interval;
- total result-root size;
- retained trace depth.

### 34.5 Shutdown

Evidence flush and close shall be bounded. A timeout shall mark evidence incomplete rather than block indefinitely.

---

## 35. Required Logging and Evidence APIs

The shared RFDS platform or `BaseInstrumentLibrary` should provide common interfaces equivalent to:

- create or attach to run context;
- create correlation and operation IDs;
- emit structured event;
- record operation start and completion;
- record error and causal chain;
- record measurement;
- attach file or binary payload;
- record device and environment identity;
- record configuration fingerprint;
- record safety and cleanup state;
- export diagnostics;
- finalize and validate evidence.

Concrete drivers shall use the common infrastructure rather than independently inventing incompatible schemas.

The public Robot Framework API may expose diagnostics and evidence export keywords as defined by RFDS-002 and the driver capability model. Internal evidence implementation details shall not be exposed as uncontrolled public keywords.

---

## 36. Required Schemas and Package Artifacts

Each driver package shall contain or reference the approved RFDS evidence schemas required for its outputs.

Recommended package structure:

```text
rf_<driver_name>/
├── schemas/
│   └── evidence/
│       ├── run_summary.schema.json
│       ├── event.schema.json
│       ├── operation.schema.json
│       ├── error.schema.json
│       ├── measurement_metadata.schema.json
│       ├── evidence_manifest.schema.json
│       └── device_identity.schema.json
├── docs/
│   └── logging_and_evidence.md
├── guide/
│   └── evidence_and_diagnostics.md
├── scripts/
│   ├── validate_evidence.ps1
│   ├── validate_evidence.bat
│   └── validate_evidence.sh
└── tests/
    └── evidence/
```

Shared schemas may be supplied by the RFDS core package when package versions and compatibility are declared.

---

## 37. Required Tests

### 37.1 Schema tests

Verify:

- all mandatory JSON and JSONL schemas validate;
- required fields are enforced;
- invalid status values are rejected;
- unknown-field policy behaves as declared;
- schema versions are present;
- JSON output contains no non-standard numeric values.

### 37.2 Correlation tests

Verify:

- run IDs are unique;
- operation and correlation IDs propagate through Robot, driver, protocol, error, measurement, and cleanup evidence;
- references resolve to existing artifacts or declared external locations;
- multi-driver and multi-process producer identities remain distinct.

### 37.3 Ordering tests

Verify:

- per-producer sequences are monotonic;
- duplicate and missing sequence numbers are detected;
- timestamps and monotonic durations are consistent;
- rotation or partitioning preserves order.

### 37.4 Robot evidence tests

Verify:

- `output.xml`, `log.html`, and `report.html` are generated;
- Robot result totals agree with `run_summary.json`;
- setup and teardown failures remain visible;
- Rebot-derived outputs reference original outputs;
- attachment links resolve.

### 37.5 CSV tests

Verify:

- UTF-8 and delimiter compliance;
- stable headers and column order;
- decimal-point handling independent of locale;
- quote and newline escaping;
- formula-injection protection;
- row count and metadata sidecar consistency;
- missing and invalid numeric value handling;
- large-file partitioning.

### 37.6 Redaction tests

Verify:

- configured secrets do not appear in logs, JSON, JSONL, CSV, Robot reports, traces, attachments, or diagnostic bundles;
- URLs and headers are sanitized;
- redaction markers and stable tokens are represented correctly;
- public evidence archives contain no private raw traces requiring restricted access.

### 37.7 Integrity tests

Verify:

- manifest enumerates all intended artifacts;
- SHA-256 hashes validate;
- unexpected modification is detected;
- missing and duplicate files are reported;
- derived artifacts identify source evidence;
- exact release-candidate identity is present for release runs.

### 37.8 Failure and recovery tests

Inject:

- disk-full or write failure;
- truncated JSONL line;
- process crash;
- attachment write failure;
- manifest-generation failure;
- evidence-validation failure;
- logging queue overflow;
- flush timeout.

Verify that evidence loss is explicit and final status is not falsely complete.

### 37.9 Performance tests

Where high-rate or long-duration logging is required, verify:

- sustained event and sample throughput;
- bounded memory;
- rotation;
- no unacceptable impact on driver timing;
- correct dropped-record counters;
- deterministic finalization.

### 37.10 Cross-specification tests

Verify consistency with:

- RFDS-007 error codes;
- RFDS-009 test status and HIL identity;
- RFDS-012 GUI operation records;
- RFDS-014 configuration fingerprints;
- RFDS-015 plugin evidence;
- RFDS-017 contract identity;
- RFDS-018 bench identity;
- RFDS-019 protocol vector and trace references;
- RFDS-011 release manifest.

---

## 38. Required Execution Workflow

### Step 1 — Allocate run context

- create run ID and result root;
- initialize evidence producer;
- record start time and execution mode;
- reserve unique output paths.

### Step 2 — Capture environment

- record software, platform, dependency, source, and package identity;
- record schema versions;
- record clock status.

### Step 3 — Capture configuration and contracts

- validate and fingerprint effective configuration;
- record RFDS-017, RFDS-018, capability, plugin, and protocol-vector identities as applicable;
- redact secrets.

### Step 4 — Capture device or simulator identity

- record transport and identity;
- distinguish real hardware from simulation;
- record fixture and reference instruments where applicable.

### Step 5 — Execute and correlate

- propagate run, correlation, operation, session, Robot, protocol, and sample identifiers;
- record events, errors, measurements, traces, and attachments.

### Step 6 — Preserve cleanup and final state

- record stop, abort, emergency, teardown, and safe-state evidence;
- preserve original and cleanup failures separately.

### Step 7 — Generate Robot and derived reports

- finalize Robot outputs;
- generate CSV, summaries, plots, or PDFs from authoritative data;
- record source references and tool versions.

### Step 8 — Finalize evidence

- flush and close files;
- calculate counts and statuses;
- generate run summary;
- generate manifest and checksums;
- validate schemas, references, sequences, and integrity.

### Step 9 — Publish or archive

- apply retention and access policy;
- create diagnostic or release evidence bundle where required;
- record final archive hash.

---

## 39. Acceptance Criteria

An implementation passes RFDS-008 only when:

1. every formal run has one unique run ID and isolated result root;
2. required Robot runs produce `output.xml`, `log.html`, and `report.html`;
3. authoritative and derived evidence are explicitly distinguished;
4. all applicable events, operations, errors, measurements, protocol exchanges, safety actions, and cleanup records are correlated;
5. machine-readable evidence uses declared, validated schema versions;
6. timestamps include timezone and durations use a monotonic source where available;
7. JSON, JSONL, and canonical CSV comply with this specification;
8. driver, software, configuration, execution mode, and applicable device/bench identities are recorded;
9. real-hardware and simulation evidence cannot be confused;
10. requested, setpoint, read-back, measured, and calculated values remain distinguishable;
11. units, limits, validity, and pass/fail oracles are explicit where applicable;
12. required raw evidence is preserved or referenced with integrity information;
13. cleanup and safe-state evidence remains visible even after earlier failure;
14. secrets and prohibited sensitive values are absent from distributable evidence;
15. dropped, truncated, missing, or failed evidence is reported explicitly;
16. the run summary agrees with Robot and structured evidence totals;
17. the evidence manifest lists required files and validates their SHA-256 hashes;
18. derived reports reference their authoritative source evidence;
19. release and gate evidence is tied to the exact candidate revision;
20. all required evidence validation tests pass.

---

## 40. Failure Conditions

RFDS-008 shall fail when any applicable condition occurs:

- formal Robot evidence omits `output.xml`, `log.html`, or `report.html`;
- a PASS result has no traceable authoritative evidence;
- a derived report contradicts authoritative evidence without declaring the conflict;
- test, operation, protocol, measurement, error, or cleanup evidence cannot be correlated;
- real-hardware and simulator results are mixed or mislabeled;
- requested and measured values are silently conflated;
- units or limits required to interpret a result are absent;
- secrets or prohibited private data appear in evidence;
- evidence files are overwritten across runs;
- missing or dropped records are not reported;
- timestamps are ambiguous or lack timezone in machine-readable evidence;
- non-standard or invalid JSON is produced;
- CSV output is locale-dependent, structurally ambiguous, or unsafe for normal spreadsheet opening;
- cleanup failure is hidden;
- evidence claims physical verification without a physical oracle;
- evidence belongs to a different package or source revision;
- manifest hashes do not validate;
- finalized reviewed evidence is modified without re-manifesting and re-review;
- mandatory evidence remains incomplete or corrupt;
- release documentation overstates the available evidence level.

---

## 41. Lifecycle Integration

### Gate 1 — Architecture and Skeleton

Deliver:

- evidence architecture and run-context design;
- schema skeletons;
- standard identifiers and context propagation;
- result-directory policy;
- redaction policy;
- basic operational logging;
- evidence unit-test skeleton.

### Gate 2 — Core Implementation

Deliver:

- structured event and operation logging;
- environment, driver, and configuration identity;
- Robot artifact generation;
- error and cleanup evidence;
- canonical run summary;
- initial CSV and JSON exports.

### Gate 3 — Extended Features

Deliver as applicable:

- measurement streams;
- protocol and RFDS-019 correlation;
- multi-driver and multi-process correlation;
- attachments and plots;
- rotation, compression, crash recovery, and diagnostic bundles;
- configuration migration evidence;
- GUI and plugin evidence integration.

### Gate 4 — Tests and Documentation

Deliver:

- schema, correlation, Robot, CSV, redaction, integrity, failure, and performance tests;
- evidence validation scripts;
- logging and evidence documentation;
- troubleshooting and diagnostic-bundle guide;
- verified examples;
- generated sample evidence.

### Gate 5 — Review and Release

Verify:

- exact-candidate evidence binding;
- manifest and hashes;
- secret scanning;
- cross-specification consistency;
- test, conformance, HIL, and review evidence completeness;
- release evidence archive;
- history, review, README, GitHub Pages, and release-note status.

---

## 42. Change Control

Whenever an evidence schema, field meaning, status, filename, directory, identifier, redaction rule, correlation rule, or authoritative-source decision changes, the same revision shall update:

- schema files and schema versions;
- evidence writer and validator;
- documentation and examples;
- tests;
- migration or compatibility rules;
- AI and GUI contracts where affected;
- history and review records;
- release notes when public consumers are affected.

A breaking evidence-schema change without a new major schema version and migration or compatibility statement shall fail release review.

A public driver behaviour change that affects arguments, results, errors, state, protocol, measurements, or cleanup shall update the relevant evidence schema or mapping in the same driver revision.

---

## 43. Review Checklist

1. Does every run receive a unique run ID and isolated output directory?
2. Are authoritative and derived artifacts distinguished?
3. Is Robot `output.xml` preserved as the authoritative Robot result?
4. Are `log.html` and `report.html` generated and linked?
5. Do run, suite, test, keyword, operation, protocol, sample, error, and cleanup references correlate?
6. Are timestamps UTC and timezone-aware?
7. Are monotonic durations used where needed?
8. Are JSON and JSONL schemas declared and validated?
9. Is canonical CSV UTF-8, locale-independent, stable, and safely escaped?
10. Are row counts, hashes, and metadata sidecars correct?
11. Are requested, read-back, measured, and calculated values distinct?
12. Are units, limits, validity, and status explicit?
13. Is real hardware clearly separated from simulation or replay?
14. Are driver, package, source revision, configuration, device, firmware, fixture, and bench identities recorded as applicable?
15. Are RFDS-017, RFDS-018, capability, configuration, plugin, and RFDS-019 identities or hashes recorded where applicable?
16. Are raw protocol and measurement observations preserved where required?
17. Are errors, causal chains, retries, recovery, and cleanup recorded without hiding the original failure?
18. Is safe-state confidence represented honestly?
19. Are dropped events, dropped samples, truncation, and write failures visible?
20. Are secrets absent from every distributable artifact?
21. Does the diagnostic bundle apply the redaction policy?
22. Does the evidence manifest enumerate every required artifact?
23. Do SHA-256 hashes validate?
24. Do derived reports identify their source evidence and tool version?
25. Is evidence tied to the exact reviewed release candidate?
26. Are retention, compression, and archive rules documented?
27. Do crash-recovery and disk-failure tests behave correctly?
28. Are logging throughput and memory bounded for the supported workload?
29. Are RFDS-009, RFDS-012, RFDS-014, RFDS-015, RFDS-019, and release evidence consistent?
30. Are all acceptance criteria satisfied?

---

## 44. Minimum Definition of Done

RFDS-008 implementation is complete for a released driver when:

- a common run context and structured evidence system are implemented;
- Robot Framework artifacts are generated for every formal Robot run;
- run summaries, environment records, identities, configuration fingerprints, events, errors, cleanup, and integrity records are produced;
- applicable measurements use the canonical CSV or JSONL model;
- applicable protocol exchanges link to RFDS-019 vectors and traces;
- simulation and real-device evidence are unmistakably separated;
- secrets are redacted and automated scans pass;
- evidence finalization detects loss, truncation, and corruption;
- the evidence manifest and SHA-256 hashes validate;
- required tests pass;
- documentation and diagnostic-bundle procedures are complete;
- no mandatory release or qualification evidence is incomplete, corrupt, or tied to another revision;
- all acceptance criteria in Section 39 pass.

---

## 45. Goal

Provide consistent, trustworthy, machine-readable, reviewable, and auditable proof of what every RFDS driver, test, GUI, simulator, bench, and release actually did.

The standard shall make it difficult to confuse:

- a log message with proof;
- a derived report with raw evidence;
- a simulator result with physical validation;
- a commanded safe state with a verified safe state;
- a test from another revision with current release evidence;
- a PASS result with a complete and reviewable evidence package.

---

## Appendix A — Example Operation Event

```json
{
  "schema": "rfds.operation_event",
  "schema_version": "1.0.0",
  "run_id": "run-20260727T081530.412Z-7f3a21c8",
  "producer_id": "rf_keysight_n6700:PSU_MAIN",
  "sequence": 124,
  "timestamp_utc": "2026-07-27T08:15:31.004Z",
  "monotonic_ns": 5830123491234,
  "event_type": "OPERATION_COMPLETED",
  "level": "INFO",
  "suite_id": "suite-psu-efficiency",
  "test_id": "test-vin-12v",
  "keyword_id": "kw-00341",
  "correlation_id": "corr-step-00045",
  "operation_id": "op-000092",
  "source": {
    "origin": "ROBOT_FRAMEWORK",
    "driver_id": "keysight_n6700",
    "driver_version": "26.03",
    "session_alias": "PSU_MAIN",
    "capability_id": "CAP-SET-DC-VOLTAGE",
    "keyword": "Set DC Voltage"
  },
  "arguments": {
    "channel": 1,
    "voltage": 5.0
  },
  "execution": {
    "mode": "REAL_HARDWARE",
    "profile": "SAFE_OUTPUT",
    "timeout_s": 10.0,
    "retries": 0,
    "transmission_occurred": true,
    "duration_s": 0.246
  },
  "result": {
    "status": "PASS",
    "return_value": null,
    "state_after": "CONNECTED"
  },
  "cleanup": {
    "required": false,
    "status": "NOT_APPLICABLE"
  },
  "evidence_refs": [
    "protocol/exchanges.jsonl#px-000092",
    "events/operations.jsonl#124",
    "robot/output.xml#kw-00341"
  ]
}
```

---

## Appendix B — Example Measurement CSV

```csv
schema_version,run_id,suite_id,test_id,correlation_id,operation_id,sample_id,sequence,timestamp_utc,elapsed_s,source_driver_id,session_alias,device_id,channel,quantity,value,unit,value_kind,validity,status,requested_value,requested_unit,lower_limit,upper_limit,limit_unit,error_percent,raw_reference,calculation_id,notes
1.0.0,run-20260727T081530.412Z-7f3a21c8,suite-psu-efficiency,test-vin-12v,corr-step-00045,op-meas-000093,sample-000001,1,2026-07-27T08:15:31.612Z,1.200,hp34401a,DMM_INPUT,dut-psu-01,INPUT,VOLTAGE_DC,12.0012,V,MEASURED,VALID,PASS,12.0,V,11.88,12.12,V,0.010,,,
1.0.0,run-20260727T081530.412Z-7f3a21c8,suite-psu-efficiency,test-vin-12v,corr-step-00045,op-calc-000095,sample-000001,2,2026-07-27T08:15:31.620Z,1.208,rfds_calculation,POWER_EFFICIENCY,dut-psu-01,,EFFICIENCY,81.42,%,CALCULATED,VALID,PASS,,,65.0,,%,,measurements/measurements.csv#row-1,CALC-EFFICIENCY-v1,
```

---

## Appendix C — Example Evidence Manifest Entry

```json
{
  "path": "robot/output.xml",
  "role": "AUTHORITATIVE_RESULT",
  "media_type": "application/xml",
  "schema": "robot.output",
  "schema_version": "7.x",
  "size_bytes": 184220,
  "sha256": "4f9897b9d0d10b3f3a...",
  "finalized_at": "2026-07-27T08:18:12.441Z",
  "producer": {
    "name": "Robot Framework",
    "version": "7.3"
  },
  "authoritative": true,
  "derived_from": [],
  "completeness": "COMPLETE",
  "redaction": "NOT_REQUIRED",
  "retention_class": "HIL_QUALIFICATION"
}
```

---

## Appendix D — Example Run Summary

```json
{
  "schema": "rfds.run_summary",
  "schema_version": "1.0.0",
  "run_id": "run-20260727T081530.412Z-7f3a21c8",
  "activity": "HIL_ROBOT_TEST",
  "execution_mode": "REAL_HARDWARE",
  "start_time_utc": "2026-07-27T08:15:30.412Z",
  "end_time_utc": "2026-07-27T08:18:12.441Z",
  "duration_s": 162.029,
  "status": "PASS",
  "evidence_completeness": "COMPLETE",
  "driver": {
    "id": "keysight_n6700",
    "version": "26.03",
    "source_revision": "git:3f9a2d1",
    "package_sha256": "9e8a..."
  },
  "robot": {
    "version": "7.3",
    "passed": 12,
    "failed": 0,
    "skipped": 0,
    "output": "robot/output.xml",
    "log": "robot/log.html",
    "report": "robot/report.html"
  },
  "safety": {
    "safe_start": "VERIFIED",
    "safe_teardown": "VERIFIED"
  },
  "evidence_counts": {
    "events": 824,
    "operations": 146,
    "measurements": 220,
    "protocol_exchanges": 188,
    "errors": 0,
    "dropped_events": 0,
    "dropped_samples": 0,
    "incomplete_artifacts": 0
  },
  "limitations": [
    "This run validates the declared safe-output profile only."
  ],
  "manifest": "evidence_manifest.json",
  "redaction_status": "PASS"
}
```

---

## Appendix E — Evidence Authority Examples

| Question | Authoritative evidence | Derived evidence |
|---|---|---|
| Did a Robot test pass? | `robot/output.xml` | `report.html`, Markdown summary |
| What protocol bytes were transmitted? | raw transport trace or binary capture | formatted hexdump, HTML log |
| What value was measured? | canonical measurement CSV/JSONL and raw instrument result | plot, PDF table |
| Which package was tested? | environment/package identity and package hash | README statement |
| Was safe state achieved? | declared oracle and final-state evidence | console message saying cleanup completed |
| Which tests cover a requirement? | requirement coverage matrix plus executed test references | narrative review summary |

---

## Appendix F — Changes in Version 1.0

Version 1.0 establishes:

- the RFDS evidence principles and classification model;
- evidence levels E0 through E4;
- run, correlation, operation, protocol, sample, and attachment identifiers;
- UTC timestamp, monotonic duration, and event sequencing rules;
- canonical result-directory layout;
- mandatory Robot Framework evidence;
- structured JSON and JSONL event envelopes;
- canonical long-form measurement CSV;
- protocol, error, safety, cleanup, configuration, and identity evidence;
- redaction and spreadsheet-safety rules;
- manifest, SHA-256 integrity, provenance, and completeness requirements;
- crash recovery, storage, retention, diagnostic-bundle, and performance rules;
- lifecycle deliverables, acceptance criteria, failure conditions, review checklist, and definition of done;
- integration with RFDS-009, RFDS-012, RFDS-014, RFDS-015, RFDS-017, RFDS-018, RFDS-019, and RFDS-011.
