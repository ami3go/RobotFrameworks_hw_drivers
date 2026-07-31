# RFDS-001 — Platform Requirements

## Overall Project Goals, Governance, and Architecture

**Version:** 1.1  
**Document ID:** RFDS-001  
**Status:** Review candidate  
**Applies to:** All RFDS Robot Framework driver projects, shared platform components, protocol simulators, test benches, examples, validation suites, repositories, and release packages

---

## 1. Purpose

This specification defines the top-level goals, governance model, architecture, mandatory platform boundaries, release classes, and project-wide acceptance requirements for the RFDS Robot Framework Driver Platform.

RFDS-001 is the parent platform specification. It establishes the common model that all device-specific drivers and all subordinate RFDS specifications shall follow.

**RFDS-001-PUR-001 — Platform purpose**  
The platform shall provide a consistent and production-oriented method to:

1. implement Python drivers for laboratory, industrial, embedded, and test equipment;
2. expose those drivers as stable Robot Framework libraries;
3. describe each driver in a machine-readable form that an AI agent can safely use;
4. combine multiple drivers into an AI-readable test-bench model;
5. verify that each public Robot Framework keyword reaches the intended device protocol operation;
6. generate repeatable tests, examples, evidence, reviews, and release packages;
7. preserve compatibility, safety, traceability, and maintainability across driver revisions;
8. determine objectively whether a driver release is experimental, simulator-validated, hardware-validated, production-ready, or bench-integrated.

---

## 2. Platform Vision

**RFDS-001-VIS-001 — Coherent driver ecosystem**  
The RFDS platform shall make heterogeneous hardware drivers behave as members of one coherent automation ecosystem rather than as unrelated scripts or vendor-specific libraries.

A user, test developer, operator, or AI agent shall be able to:

- identify a driver and its supported device;
- install the driver package in a clean declared environment;
- connect to the device through a declared transport profile;
- discover and call documented Robot Framework keywords;
- understand keyword preconditions, postconditions, side effects, timing, safety, and return values;
- combine the driver with other drivers in a defined bench topology;
- execute examples and conformance tests;
- inspect traceable evidence showing what was called and what protocol operation occurred;
- update to a compatible revision without unnecessary changes to existing Robot Framework tests.

**RFDS-001-VIS-002 — Platform priorities**  
The platform shall prioritize correctness, deterministic behaviour, safe hardware control, finite execution, clear failure reporting, reproducibility, and long-term API stability.

---

## 3. Project Goals

### 3.1 Primary goals

**RFDS-001-GOAL-001 — Primary platform goals**  
The RFDS platform shall:

1. provide a unified Robot Framework driver architecture;
2. standardize public keyword design and driver lifecycle management;
3. support real hardware and approved protocol simulators;
4. separate test intent from device semantics, protocol implementation, and transport I/O;
5. provide machine-readable contracts for AI-assisted planning and test generation;
6. provide objective callability and protocol-conformance evidence;
7. support small, reviewable, gate-based implementation increments;
8. produce self-contained, versioned, GitHub-ready release packages;
9. maintain traceability from requirements to implementation, tests, evidence, and release history;
10. support safe integration of multiple instruments, fixtures, relays, DUTs, and measurement paths;
11. support automated release validation through stable manifests and evidence schemas.

### 3.2 Quality goals

**RFDS-001-GOAL-002 — Released-driver qualities**  
A production-class released driver shall be:

- predictable;
- testable;
- traceable;
- maintainable;
- documented;
- installable;
- recoverable after supported communication faults;
- safe for its declared operating profile;
- understandable without reading the complete source code;
- usable from Robot Framework and, where declared, from Python;
- verifiable using machine-readable release evidence.

### 3.3 AI-assistance goals

**RFDS-001-GOAL-003 — AI planning support**  
The platform shall provide enough structured information for an AI agent to:

- select the correct driver and keyword;
- construct valid keyword arguments;
- satisfy connection and state preconditions;
- respect resource conflicts and safety constraints;
- plan setup, execution, verification, recovery, and teardown;
- interpret return values and failures;
- generate multi-driver Robot Framework test plans;
- identify unknown, ambiguous, or unsupported operations instead of inventing behaviour.

---

## 4. Scope Boundary

### 4.1 In scope

**RFDS-001-SCP-001 — Platform scope**  
RFDS-001 covers:

- RFDS governance and document hierarchy;
- release classes and requirement applicability;
- overall platform architecture;
- mandatory driver layers and responsibility boundaries;
- canonical package and repository model;
- common Robot Framework lifecycle capability profile;
- Python driver architecture principles;
- transport and protocol abstraction principles;
- AI driver and test-bench contract integration;
- lifecycle, review, versioning, deviation, and release expectations;
- testing and conformance integration;
- evidence, history, and traceability;
- safety, state ownership, cancellation, and resource-control principles;
- documentation, examples, scripts, CI validation, and GitHub publication requirements;
- compatibility and change-control rules;
- dependency, supply-chain, and release-integrity evidence.

### 4.2 Out of scope

RFDS-001 does not define:

- the complete keyword set for a specific device;
- vendor-specific command syntax;
- detailed electrical accuracy requirements;
- device calibration procedures;
- a specific bench wiring topology;
- a specific simulator implementation;
- a specific CI service vendor or hosting provider;
- exact operating-system or Python-version support for every driver;
- detailed requirements assigned to subordinate RFDS specifications.

Device-specific requirements shall be defined in the driver implementation task, driver documentation, AI contract, protocol vectors, and applicable subordinate RFDS specifications.

---

## 5. Normative Terminology

- **shall / shall not** — mandatory requirement;
- **should / should not** — recommended requirement; a deviation requires documented justification;
- **may** — permitted implementation choice;
- **driver** — the complete RFDS package exposing a device or logical hardware service;
- **driver core** — Python implementation containing device semantics independent of Robot Framework presentation where practical;
- **Robot library** — the Robot Framework-facing public API layer;
- **transport** — VISA, serial, TCP, UDP, HTTP, USB, CAN, Modbus, vendor SDK, GPIO SDK, or equivalent communication mechanism;
- **protocol operation** — command, query, request, frame, transaction, or SDK call sent toward the device boundary;
- **AI Driver Contract** — the single-driver machine-readable contract defined by RFDS-017;
- **AI Test Bench Contract** — the multi-driver system contract defined by RFDS-018;
- **conformance evidence** — recorded proof that a public Robot Framework call produced the expected protocol behaviour;
- **approved simulator** — a versioned simulator operating at the protocol boundary used by the real driver connection and approved for a declared verification scope;
- **public keyword** — a keyword intentionally exported to Robot Framework users;
- **canonical keyword** — the preferred public name for a capability;
- **alias** — an additional supported public name mapping to the same declared capability;
- **release package** — the distributable ZIP archive containing the complete driver project;
- **internal root folder** — the stable top-level folder contained inside the release ZIP;
- **release class** — the declared validation and readiness level of a release;
- **mandatory profile** — a requirement set that applies to a declared release class;
- **deviation** — an approved, traceable exception to a requirement;
- **release authority** — the person or process authorized to approve a release and any allowed deviations.

---

## 6. Requirement Identification and Traceability Rules

**RFDS-001-REQ-001 — Stable requirement identifiers**  
Every normative RFDS-001 requirement shall use a stable identifier in the form:

```text
RFDS-001-<AREA>-<NUMBER>
```

Examples:

```text
RFDS-001-ARCH-001
RFDS-001-API-003
RFDS-001-SAFE-005
RFDS-001-REL-004
```

**RFDS-001-REQ-002 — Identifier immutability**  
A published requirement identifier shall not be reused for a different requirement. Removed requirements shall be marked retired in the change record.

**RFDS-001-REQ-003 — Requirement trace chain**  
Each applicable mandatory requirement shall be traceable through equivalent records to:

```text
Requirement → implementation → verification method → result → evidence → review decision
```

**RFDS-001-REQ-004 — Subclause traceability**  
Lettered or numbered clauses beneath one requirement identifier are part of that requirement unless assigned separate identifiers.

---

## 7. Document Governance and Precedence

### 7.1 Normative hierarchy

**RFDS-001-GOV-001 — Document precedence**  
Unless legal, regulatory, contractual, or approved safety obligations require stricter controls, RFDS requirements shall be interpreted using this hierarchy:

1. applicable legal, regulatory, contractual, and approved safety requirements;
2. RFDS-001 Platform Requirements;
3. applicable subordinate RFDS specifications;
4. approved device-specific implementation specification or task;
5. approved architecture decisions and deviations;
6. informative guides, examples, and explanatory material.

A lower-level document may add stricter requirements but shall not silently weaken a higher-level requirement.

### 7.2 Authoritative subject ownership

**RFDS-001-GOV-002 — Specification ownership**  
RFDS-001 defines platform-level intent and integration rules. Detailed normative ownership is delegated as follows:

| Document | Authoritative subject |
|---|---|
| RFDS-001 | Platform goals, governance, architecture, release classes, and cross-specification acceptance |
| RFDS-002 | Mandatory public API, keyword naming, signatures, and compatibility rules |
| RFDS-003 | BaseInstrumentLibrary and common base-class design |
| RFDS-004 | Transport abstraction and supported transport behaviour |
| RFDS-005 | Driver package and repository structure |
| RFDS-006 | Python coding, typing, documentation, and logging standard |
| RFDS-007 | Exception taxonomy, diagnostics, and error representation |
| RFDS-008 | Logging, evidence, traceability, and diagnostic-bundle schema |
| RFDS-009 | Unit, simulator, integration, hardware, Robot, and regression testing |
| RFDS-010 | Production-readiness review checklist and scoring |
| RFDS-011 | Versioning, changelog, packaging, and release process |
| RFDS-012 | Generic operator-GUI integration |
| RFDS-013 | Capability discovery model |
| RFDS-014 | Configuration import, export, validation, and persistence |
| RFDS-015 | Plugin architecture and dynamic discovery |
| RFDS-017 | AI-readable contract for one driver |
| RFDS-018 | AI-readable contract for a multi-driver test bench |
| RFDS-019 | Public keyword callability and driver-to-device protocol conformance |
| RFDS-020 | Phase-and-gate implementation workflow |

Where a subject has a listed owner, RFDS-001 shall define the platform expectation and the subordinate specification shall define detailed implementation and verification rules.

### 7.3 Version applicability

**RFDS-001-GOV-003 — Exact compliance baseline**  
Each release shall record the exact revision of every RFDS specification used for validation. A newer subordinate specification shall not be assumed retroactively unless the release is revalidated against it.

### 7.4 Conflict handling

**RFDS-001-GOV-004 — Controlled conflict resolution**  
A detected conflict shall be recorded and resolved through one of:

- correction of the conflicting document;
- approved interpretation note;
- approved architecture decision;
- time-limited deviation.

Silent interpretation is prohibited.

---

## 8. Release Classes and Applicability

### 8.1 Release classes

**RFDS-001-CLS-001 — Release-class declaration**  
Every packaged revision shall declare exactly one release class:

| Class | Name | Meaning |
|---|---|---|
| D0 | Development | Experimental artifact; incomplete verification permitted and clearly marked |
| D1 | Simulator validated | Public API and protocol behaviour validated using an approved simulator |
| D2 | Hardware validated | Representative real-device operation validated in addition to D1 evidence |
| P1 | Production driver | Release-ready driver meeting all mandatory production requirements |
| B1 | Integrated bench | Multi-driver bench release with RFDS-018 topology, resources, safety, and system validation |

### 8.2 Minimum applicability matrix

**RFDS-001-CLS-002 — Mandatory applicability**

| Requirement group | D0 | D1 | D2 | P1 | B1 |
|---|---:|---:|---:|---:|---:|
| Package identity and stable internal root | Required | Required | Required | Required | Required |
| Import and keyword discovery | Required | Required | Required | Required | Required |
| Unit tests | Required | Required | Required | Required | Required |
| Approved simulator definition | Optional | Required | Required | Required | Required where simulator is used |
| RFDS-019 simulator conformance | Optional | Required | Required | Required | Required for included drivers |
| Representative real-device validation | Optional | Optional | Required | Required | Required |
| Safety profile | Required where controllable risk exists | Required | Required | Required | Required |
| Ten useful examples | Optional | Required unless approved scope exception | Required | Required | Bench examples as applicable |
| GitHub Pages or buildable documentation source | Optional | Required | Required | Required | Required |
| Formal release manifest | Required | Required | Required | Required | Required |
| SBOM and checksums | Optional | Recommended | Required | Required | Required |
| RFDS-018 bench contract | N/A | N/A | Optional | Optional | Required |
| Formal production-readiness review | Optional | Optional | Recommended | Required | Required |

### 8.3 Applicability declaration

**RFDS-001-CLS-003 — Requirement disposition**  
Every mandatory requirement for the selected class shall have one of these dispositions:

- `PASS`;
- `FAIL`;
- `NOT_APPLICABLE` with rationale;
- `DEVIATION` with approved deviation identifier.

`NOT_RUN` shall not satisfy release acceptance.

---

## 9. Architectural Principles

All RFDS drivers shall follow these principles.

**RFDS-001-ARCH-001 — Stable public API**  
Robot Framework tests shall depend on declared public keywords, not on private methods, transport internals, or vendor-library implementation details.

**RFDS-001-ARCH-002 — Separation of concerns**  
Robot keyword presentation, device semantics, protocol serialization, transport I/O, configuration, and evidence generation shall be separated sufficiently to permit focused testing and maintenance.

**RFDS-001-ARCH-003 — Explicit state**  
Connection state, selected channel, active mode, output state, session ownership, and other operational state shall be explicit and queryable where applicable.

**RFDS-001-ARCH-004 — Deterministic behaviour**  
Given equivalent valid preconditions, arguments, device response, and configuration, a keyword shall produce the same protocol intent and an equivalent Robot Framework result.

**RFDS-001-ARCH-005 — Visible failure**  
A driver shall not report success when a required protocol operation, response, validation, safety check, or state transition failed.

**RFDS-001-ARCH-006 — Safe default behaviour**  
Initial state, disconnect behaviour, error recovery, test teardown, cancellation, and emergency handling shall prefer the safest declared device state.

**RFDS-001-ARCH-007 — Traceability**  
Public capabilities shall be traceable to implementation, documentation, AI contract entries, tests, protocol vectors where applicable, and release history.

**RFDS-001-ARCH-008 — Compatibility first**  
Existing public keywords, arguments, defaults, aliases, return schemas, error codes, and documented behaviour shall remain compatible unless a controlled breaking change is approved and versioned.

**RFDS-001-ARCH-009 — AI-readable semantics**  
Machine-readable contracts shall describe operational meaning, not merely duplicate function names and argument lists.

**RFDS-001-ARCH-010 — Evidence-based release**  
A driver shall not be considered production-ready solely because it imports or its unit tests pass. A production release shall use documented review, test, conformance, packaging, compatibility, and release-integrity evidence.

---

## 10. Logical Platform Architecture

The normative execution path is:

```text
Test requirement or operator intent
                ↓
Robot Framework test suite / AI-generated plan
                ↓
Public Robot Framework keyword API
                ↓
Driver service and device-semantics layer
                ↓
Protocol adapter / command builder / SDK adapter
                ↓
Transport boundary
                ↓
Physical device or approved protocol simulator
                ↓
Raw device response, acknowledgement, or fault
                ↓
Transport and protocol parsing
                ↓
Typed driver result or documented exception
                ↓
Robot Framework-compatible result and evidence
```

The normative planning and metadata path is:

```text
RFDS-017 AI Driver Contracts
                +
RFDS-018 AI Test Bench Contract
                +
Test requirements and safety constraints
                ↓
AI planner or human test designer
                ↓
Robot Framework suite using declared public keywords
```

The normative verification path is:

```text
Exported Robot Framework keyword inventory
                ↓
RFDS-019 call and protocol conformance suite
                ↓
Observed outbound and inbound protocol evidence
                ↓
Coverage matrix, Robot reports, traces, and review verdict
```

---

## 11. Architectural Layers

### 11.1 Test and orchestration layer

Responsibilities:

- express test intent in Robot Framework;
- coordinate setup, actions, measurements, verification, cancellation, and teardown;
- manage multi-driver workflows;
- produce Robot Framework reports;
- avoid direct use of private driver implementation details.

This layer may contain reusable Robot resource files, bench-level keywords, test templates, and test data.

### 11.2 Robot Framework API layer

Responsibilities:

- expose public keywords intentionally;
- provide stable keyword names and signatures;
- validate Robot-facing arguments;
- convert results into Robot Framework-compatible values;
- translate documented driver exceptions into actionable failures;
- provide library documentation discoverable through Libdoc;
- preserve aliases and deprecation information.

The Robot API layer shall not silently alter device semantics.

### 11.3 Driver service and device-semantics layer

Responsibilities:

- implement device capabilities and state transitions;
- enforce device-level preconditions and ranges;
- coordinate command sequences;
- apply stabilization, retry, timeout, cancellation, and recovery policy;
- define typed return models where appropriate;
- remain sufficiently independent of Robot Framework to permit focused Python testing.

### 11.4 Protocol adapter layer

Responsibilities:

- map semantic driver operations to device protocol operations;
- serialize commands, queries, frames, requests, and SDK arguments;
- apply addressing, channel selection, units, encoding, framing, termination, and checksums;
- parse raw protocol responses;
- detect malformed, incomplete, or unexpected responses;
- expose protocol evidence hooks needed by RFDS-019.

### 11.5 Transport layer

Responsibilities:

- open, maintain, and close communication sessions;
- implement read, write, query, transaction, or SDK-call primitives;
- apply timeouts and transport configuration;
- expose transport errors without misreporting success;
- permit observation or tracing at the device boundary;
- prevent indefinite blocking.

### 11.6 Device or simulator layer

The driver may communicate with:

- a physical device;
- an approved protocol simulator;
- an instrumented proxy;
- a vendor SDK connected to hardware;
- a transport spy used at the protocol boundary.

A simulator used for conformance shall preserve the protocol boundary relevant to the real connection.

### 11.7 Metadata and contract layer

Responsibilities:

- describe driver identity and capabilities;
- define preconditions, postconditions, side effects, risk, timing, retry, and resources;
- describe bench topology, resource conflicts, signal paths, and global safety;
- support machine validation and AI planning;
- remain synchronized with the released public API.

### 11.8 Validation and evidence layer

Responsibilities:

- execute unit, integration, simulator, real-device, Robot, and conformance tests;
- generate coverage and protocol evidence;
- record environment and versions;
- preserve review results, deviations, and release decisions;
- prove that mandatory acceptance criteria were met.

---

## 12. Component Responsibility Rules

**RFDS-001-CMP-001 — Public API use in tests**  
Robot Framework suites shall use public driver keywords. Raw protocol construction is permitted only in dedicated protocol-validation, diagnostic, or device-development tests where that purpose is explicit.

**RFDS-001-CMP-002 — Test-suite independence**  
A driver shall not require hidden variables or execution ordering that exists only in a particular example or test suite.

**RFDS-001-CMP-003 — Authoritative protocol knowledge**  
Command construction and response parsing shall have an authoritative implementation location and shall not be duplicated inconsistently across public keywords, tests, or examples.

**RFDS-001-CMP-004 — Externalized configuration**  
Addresses, ports, serial numbers, channels, timeouts, safety limits, and bench-specific identifiers shall not be hard-coded into reusable driver logic except for documented device defaults.

**RFDS-001-CMP-005 — Enforceable safety**  
Safety rules documented in prose or machine-readable contracts shall be implemented or verified at the responsible driver, bench, test, or operator layer. A safety statement that cannot be enforced shall be identified as advisory.

**RFDS-001-CMP-006 — Non-intrusive evidence hooks**  
Tracing, logging, or protocol observation shall not intentionally modify the semantic operation being verified.

---

## 13. Canonical Driver Package Model

### 13.1 Release ZIP naming

**RFDS-001-PKG-001 — Production ZIP name**  
An approved driver release shall use:

```text
rf_<driver_name>_v<YY>.<RR>.zip
```

Example:

```text
rf_keysight34970_v26.05.zip
```

Rules:

- `<driver_name>` shall be lowercase and filesystem-safe;
- `<YY>` shall be the two-digit release year;
- `<RR>` shall be a zero-padded, monotonically increasing release or update number within the year;
- the outer ZIP filename may change between revisions;
- the internal root folder name shall remain stable.

### 13.2 Internal root folder

**RFDS-001-PKG-002 — Stable internal root**  
The ZIP shall contain one stable top-level folder:

```text
rf_<driver_name>/
```

Example:

```text
rf_keysight34970/
```

### 13.3 Gate and development identifiers

**RFDS-001-PKG-003 — Pre-release naming**  
A development or gate artifact may append an unambiguous suffix:

```text
rf_<driver_name>_v<YY>.<RR>-g<gate>.zip
rf_<driver_name>_v<YY>.<RR>-rc<revision>.zip
```

Examples:

```text
rf_keysight34970_v26.05-g1.zip
rf_keysight34970_v26.05-g5.zip
rf_keysight34970_v26.05-rc1.zip
```

A gate or release-candidate suffix shall not be used for the approved production ZIP.

### 13.4 Fixed mandatory paths

**RFDS-001-PKG-004 — Mandatory package paths**  
RFDS-005 is the sole normative source for the exact repository and release-package structure, including whether a `src/` layout is used. RFDS-005 currently mandates a **flat layout**: the installable Python package sits directly under the stable root, with no intervening `src/` directory. Every D1, D2, P1, or B1 package shall contain at least these paths, structured per RFDS-005:

```text
rf_<driver_name>/
├── README.md
├── LICENSE
├── pyproject.toml
├── rf_<driver_name>/
├── ai/
├── tests/
├── examples/
├── scripts/
├── guide/
├── docs/
├── history/
├── review/
└── release/
```

### 13.5 Recommended implementation tree

This tree illustrates the platform-level minimum only; RFDS-005 §6 is authoritative for the complete, current canonical layout.

```text
rf_<driver_name>/
├── README.md
├── LICENSE
├── pyproject.toml
├── rf_<driver_name>/
│   ├── __init__.py
│   ├── library.py
│   ├── driver.py
│   ├── models.py
│   ├── exceptions.py
│   ├── configuration.py
│   ├── protocol/
│   └── transport/
├── ai/
│   ├── ai_contract.yaml
│   └── ai_contract.lock
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conformance/
├── examples/
│   └── index.yaml
├── scripts/
├── guide/
├── docs/
├── site/ or buildable GitHub Pages source
├── history/
├── review/
└── release/
    ├── release_manifest.yaml
    ├── requirements_traceability.csv
    ├── compatibility_report.json
    ├── checksums.sha256
    └── sbom.json
```

### 13.6 Alternative layout control

**RFDS-001-PKG-005 — Controlled equivalent layouts**  
An equivalent layout may be used only when:

1. all mandatory content remains present;
2. the alternative is required by tooling, compatibility, or repository policy;
3. every alternative path is declared in `release/release_manifest.yaml`;
4. automated package validation can resolve the mapped paths;
5. the release review approves the deviation or mapping.

### 13.7 Mandatory release content

**RFDS-001-PKG-006 — Mandatory content**  
Every P1 driver release shall include:

- a `history/` folder describing changes for the release;
- a `review/` folder containing applicable code, architecture, API, documentation, compatibility, and release reviews;
- an `examples/` folder containing at least ten useful examples unless an approved scope exception exists;
- scripts to run examples and applicable test suites;
- an up-to-date GitHub `README.md`;
- up-to-date GitHub Pages documentation or buildable source;
- a `guide/` folder explaining setup of Python, PyCharm, Robot Framework, dependencies, the driver, and example execution;
- test artifacts required by applicable RFDS specifications;
- current AI contract files;
- version, compatibility, dependency, integrity, and release metadata.

---

## 14. Release Manifest and Integrity Evidence

### 14.1 Release manifest

**RFDS-001-MAN-001 — Authoritative release manifest**  
Every packaged revision shall provide `release/release_manifest.yaml` as the authoritative machine-readable package index.

It shall contain at least:

```yaml
schema_version: "1.0"
driver_name: rf_keysight34970
release_version: "26.05"
api_version: "1.0"
release_class: P1
entry_point: rf_keysight34970.library

supported_devices: []
supported_transports: []
python_versions: []
robot_framework_versions: []

rfds_compliance:
  RFDS-001: "1.1"
  RFDS-017: "3.0"
  RFDS-018: "1.0"
  RFDS-019: "1.1"

paths:
  source: src
  ai_contract: ai/ai_contract.yaml
  tests: tests
  examples: examples
  documentation: docs
  history: history
  review: review

conformance:
  result: PASS
  evidence_path: tests/conformance/results

approved_deviations: []
```

### 14.2 Integrity records

**RFDS-001-MAN-002 — Checksums**  
P1 and B1 releases shall provide checksums for release files in `release/checksums.sha256`.

**RFDS-001-MAN-003 — Software bill of materials**  
D2, P1, and B1 releases shall provide a machine-readable software bill of materials or equivalent dependency inventory in `release/sbom.json`.

**RFDS-001-MAN-004 — Traceability index**  
P1 and B1 releases shall provide `release/requirements_traceability.csv` or an equivalent machine-readable record containing requirement ID, applicability, implementation reference, verification reference, result, evidence reference, and deviation ID where applicable.

---

## 15. Public Robot Framework API Requirements

### 15.1 Discoverability and export control

**RFDS-001-API-001 — Discoverable public API**  
The library shall import successfully and expose its intended public keywords through Robot Framework discovery and Libdoc.

**RFDS-001-API-002 — Explicit export**  
Private helpers shall not become public Robot Framework keywords accidentally. The library shall use explicit keyword export control or an equivalent deterministic mechanism.

### 15.2 Canonical common lifecycle profile

**RFDS-001-API-003 — Common lifecycle capability names**  
When the corresponding capability is supported, the canonical public keyword name shall be:

```text
Connect
Disconnect
Is Connected
Get Identity
Get Driver Information
Get Device Errors
Clear Device Errors
Reset Device
Enter Safe State
```

A device that does not support one of these capabilities may omit it. A different legacy name may remain as an alias, but shall not replace the canonical name in a new P1 release.

Detailed signatures and compatibility rules belong to RFDS-002.

### 15.3 Naming

**RFDS-001-API-004 — Keyword naming**  
Public keyword names shall:

- describe user intent;
- use consistent project vocabulary;
- avoid unnecessary vendor abbreviations where a clear generic term exists;
- remain unique after Robot Framework name normalization;
- have one canonical name;
- identify aliases explicitly.

### 15.4 Signatures

**RFDS-001-API-005 — Public signature contract**  
Every public keyword shall define:

- required arguments;
- optional arguments and defaults;
- accepted types or formats;
- units where applicable;
- return type and schema;
- stable error codes or failure categories;
- connection and state preconditions;
- side effects;
- timeout and cancellation behaviour where applicable.

### 15.5 Return values

**RFDS-001-API-006 — Stable Robot-compatible results**  
Return values shall be Robot Framework-compatible and shall use stable, documented schemas. Opaque vendor objects shall not be the only public result unless an explicit advanced API documents that behaviour.

### 15.6 Connection lifecycle

**RFDS-001-API-007 — Connection lifecycle contract**  
Each connection-capable driver shall define and test:

- connect behaviour;
- repeated-connect behaviour;
- communication verification;
- disconnect behaviour;
- repeated-disconnect behaviour;
- timeout policy;
- session ownership;
- multi-device handling where supported;
- recovery policy;
- safe-state expectations;
- whether implicit connection is prohibited or allowed.

### 15.7 Idempotency and side effects

**RFDS-001-API-008 — Idempotency declaration**  
Keywords expected to be idempotent shall be documented and tested as such. Keywords with cumulative, destructive, irreversible, or hazardous effects shall state those side effects explicitly.

### 15.8 Deprecation

**RFDS-001-API-009 — Deprecation control**  
Deprecated keywords shall remain discoverable for the approved compatibility interval, identify the replacement, preserve documented behaviour during that interval, and have a documented removal release.

---

## 16. Error and Exception Model

**RFDS-001-ERR-001 — Common exception categories**  
Drivers shall map applicable failures into the common RFDS categories defined by RFDS-007. RFDS-007 is the sole normative source for exact exception class names, hierarchy, and error codes; the platform-level view below is illustrative only and shall be read as a summary of RFDS-007's top-level taxonomy, not an alternative definition:

```text
DriverError
├── DriverConfigurationError
├── DriverValidationError
├── DriverStateError
├── DriverConnectionError
├── DriverTransportError        (includes DriverTimeoutError)
├── DriverProtocolError
├── DriverDeviceError
├── DriverResourceError
├── DriverSafetyError
├── DriverDependencyError
└── DriverInternalError
```

**RFDS-001-ERR-002 — Stable machine-readable error identity**  
A public failure shall provide a stable error category or code in addition to actionable human-readable text where the public return or exception model permits.

**RFDS-001-ERR-003 — Error context**  
Errors shall:

- include actionable context;
- avoid exposing credentials or secrets;
- preserve the original cause for diagnostic logging;
- identify whether the failed operation may have partially changed device state;
- never convert a failed required operation into a silent pass.

---

## 17. Python Driver Requirements

**RFDS-001-PY-001 — Python architecture**  
The Python implementation shall:

- use clear modules and responsibility boundaries;
- provide a stable entry point for the Robot library;
- validate arguments before unsafe or invalid transmission where possible;
- use typed interfaces or clear runtime validation for important public data;
- avoid global mutable session state unless justified;
- close resources deterministically;
- support dependency injection or equivalent seams for transport testing;
- expose protocol-boundary observation sufficient for conformance verification;
- avoid unbounded loops, reads, waits, and retries;
- preserve causal error information;
- document thread-safety and concurrency limitations;
- support repeatable installation from declared metadata.

---

## 18. Transport and Protocol Requirements

**RFDS-001-IO-001 — Supported transport declaration**  
Each driver shall declare all supported transport profiles and the configuration required for each profile.

**RFDS-001-IO-002 — Finite blocking operations**  
All blocking I/O shall have a finite timeout or a documented externally interruptible control mechanism.

**RFDS-001-IO-003 — Protocol serialization**  
Protocol operations shall apply the documented command syntax, framing, addressing, encoding, termination, payload layout, checksums, and units.

**RFDS-001-IO-004 — Response validation**  
The driver shall validate relevant response framing, structure, type, units, and integrity before reporting success.

**RFDS-001-IO-005 — Command-only operations**  
Operations that intentionally have no response shall be marked explicitly and shall not wait for an undefined response.

**RFDS-001-IO-006 — Device error checks**  
Where the device provides an error queue, status register, acknowledgement, exception response, or equivalent error mechanism, the driver shall define when and how it is checked.

**RFDS-001-IO-007 — Recovery visibility**  
Recoverable transport or protocol failures shall have documented recovery behaviour. Recovery shall not conceal the original failed operation.

**RFDS-001-IO-008 — Protocol observation**  
The implementation shall permit capture of the protocol exchange close enough to the device boundary to prove what was transmitted and received.

---

## 19. State Ownership, Cancellation, and Recovery

### 19.1 State model

**RFDS-001-STATE-001 — Declared operational states**  
Each connection-capable driver shall declare equivalent states for:

```text
initial state
connected idle state
active operation state
normal disconnect state
operation-failure state
emergency safe state
```

These six conceptual states are platform-level minimums, not a naming standard. RFDS-003 is the sole normative source for the exact connection/session state enum (names, casing, and full value set); subordinate specifications and driver implementations shall use the RFDS-003 enum rather than inventing an equivalent one.

### 19.2 State ownership

**RFDS-001-STATE-002 — State ownership policy**  
The driver shall declare:

- which device state it owns;
- which state may be externally modified;
- whether connection changes device configuration;
- whether disconnect restores, preserves, or resets configuration;
- whether a failed operation may leave a partial state change;
- how state is resynchronized after external changes.

### 19.3 Long-running operations

**RFDS-001-STATE-003 — Cooperative cancellation**  
Long-running scans, acquisitions, calibration operations, stabilization waits, or multi-step procedures shall provide a documented cooperative cancellation mechanism where interruption is operationally required.

The cancellation contract shall define:

- cancellation entry point;
- maximum expected cancellation latency;
- cleanup and safe-state behaviour;
- treatment of partial results;
- worker-thread or task cleanup;
- communication recovery verification after cancellation.

### 19.4 Recovery verification

**RFDS-001-STATE-004 — Known-good recovery call**  
After a documented recoverable communication or cancellation fault, testing shall execute a known-good public keyword and verify successful communication or successful re-establishment of the session.

---

## 20. AI Driver Contract Integration

**RFDS-001-AI-001 — Required AI Driver Contract**  
Each D1, D2, P1, and B1 driver shall provide:

```text
ai/
├── ai_contract.yaml
└── ai_contract.lock
```

The RFDS-017 AI Driver Contract shall describe one driver and include the information required by the applicable RFDS-017 revision.

**RFDS-001-AI-002 — Contract/API synchronization**  
The released AI contract shall match the released public Robot Framework API. A public capability added, removed, renamed, aliased, deprecated, or changed shall update the contract in the same revision.

### 20.1 AI contract lock

**RFDS-001-AI-003 — Lock-file purpose**  
`ai_contract.lock` shall provide at least:

```yaml
contract_schema_version: "3.0"
driver_release_version: "26.05"
api_version: "1.0"
contract_sha256: "..."
keyword_inventory_sha256: "..."
validation_tool_version: "..."
validation_timestamp: "..."
validation_result: PASS
```

The lock file shall permit detection of a stale or mismatched contract.

---

## 21. AI Test Bench Contract Integration

**RFDS-001-BENCH-001 — Required B1 system contract**  
A B1 multi-instrument bench shall provide an RFDS-018 system contract:

```text
system_ai_contract.yaml
```

The bench contract shall combine installed driver contracts into a coherent laboratory model and include the information required by the applicable RFDS-018 revision.

**RFDS-001-BENCH-002 — Driver semantic authority**  
The bench contract shall not redefine driver keyword semantics inconsistently with the corresponding RFDS-017 contract.

---

## 22. Conformance Architecture

**RFDS-001-CONF-001 — RFDS-019 integration**  
Each D1, D2, P1, and B1 driver shall integrate the applicable RFDS-019 call and protocol conformance model.

For every supported public Robot Framework keyword, the platform shall be able to determine:

- whether the keyword is exported and discoverable;
- whether it can be called through Robot Framework;
- whether it is device-facing;
- which driver operation it invokes;
- which protocol vector applies;
- what outbound operation is expected;
- what inbound response or no-response behaviour is expected;
- what Robot Framework-compatible result is expected;
- what protocol faults and recovery behaviour apply;
- where the trace evidence is stored.

**RFDS-001-CONF-002 — No silent omission**  
A public device-facing keyword shall not be silently omitted from conformance coverage.

**RFDS-001-CONF-003 — Boundary observation**  
The conformance test shall operate through the public Robot Framework API and observe the protocol boundary rather than proving only an internal mocked method call.

---

## 23. Simulator Approval Model

**RFDS-001-SIM-001 — Simulator declaration**  
A simulator used for mandatory evidence shall have a versioned profile containing at least:

- simulator identity and version;
- represented device or protocol revision;
- protocol boundary reproduced;
- supported commands and queries;
- unsupported behaviours;
- state model;
- timing model and known timing differences;
- error, timeout, malformed-response, and disconnect injection capabilities;
- known differences from physical hardware;
- approval scope.

**RFDS-001-SIM-002 — Simulator evidence boundary**  
A simulator pass shall not be represented as proof of physical measurement accuracy, electrical performance, calibration, device-specific timing, or hardware safety unless independently verified.

---

## 24. Testing Strategy

### 24.1 Mandatory test levels

**RFDS-001-TEST-001 — Production test levels**  
A P1 driver shall execute all applicable mandatory test levels:

1. static and package-layout validation;
2. Python unit tests;
3. protocol serialization and parsing tests;
4. transport-adapter tests;
5. approved simulator integration tests;
6. Robot Framework import, keyword discovery, and callability tests;
7. RFDS-019 protocol conformance tests;
8. representative real-device tests;
9. safety, timeout, cancellation, and recovery tests;
10. regression tests for corrected reproducible defects;
11. compatibility tests for changed public interfaces;
12. performance, soak, or concurrency tests where required by the device scope.

### 24.2 Test independence

**RFDS-001-TEST-002 — Independent execution**  
Tests shall declare prerequisites and shall not rely on undocumented ordering or residue from a previous run.

### 24.3 Hardware profiles

**RFDS-001-TEST-003 — Hardware test profiles**  
Real-device tests shall use declared profiles describing:

- device address or identifier;
- transport configuration;
- fixture requirements;
- allowed and prohibited operations;
- startup state;
- safe shutdown state;
- operator actions;
- evidence capture.

### 24.4 Regression tests

**RFDS-001-TEST-004 — Defect regression coverage**  
Every reproducible corrected Critical or Major defect shall receive a regression test at the lowest effective layer and, where user-visible, at the Robot Framework layer. A missing deterministic regression test requires an approved deviation.

### 24.5 Compatibility tests

**RFDS-001-TEST-005 — Public-interface compatibility testing**  
A compatibility test shall be added whenever a revision changes or corrects a public keyword name, alias, argument, default, return schema, error code, configuration key, import path, or documented command.

---

## 25. CI and Automated Validation Baseline

**RFDS-001-CI-001 — Required validation jobs**  
P1 and B1 releases shall provide a repeatable local or CI workflow covering applicable jobs:

```text
package-layout validation
clean-environment installation
Python linting
static type checking
unit tests
Robot Framework import and Libdoc generation
public keyword inventory validation
AI contract schema and lock validation
protocol-vector validation
RFDS-019 conformance
documentation build
internal-link and version-consistency checks
example smoke tests
dependency, licence, vulnerability, and secret checks
release-manifest and checksum verification
```

RFDS-001 does not mandate a specific CI service vendor.

**RFDS-001-CI-002 — Clean-environment proof**  
A P1 release shall demonstrate installation and execution of its declared basic workflow in a clean declared environment.

---

## 26. Safety Architecture

**RFDS-001-SAFE-001 — Safety enforcement level**  
Safety requirements may exist at keyword, driver, device, fixture, bench, test-plan, or operator-procedure level. The responsible enforcement layer shall be stated.

**RFDS-001-SAFE-002 — Safe initialization**  
Connection or library initialization shall not unintentionally enable hazardous outputs or change device state unless explicitly documented and approved.

**RFDS-001-SAFE-003 — Safe teardown**  
Suite teardown, disconnect, exception cleanup, cancellation, and emergency shutdown shall place affected resources into the safest achievable declared state.

**RFDS-001-SAFE-004 — Configurable limits**  
Voltage, current, power, temperature, speed, pressure, relay topology, resistance, channel, or other applicable limits shall be configurable, documented, and validated at the responsible layer.

**RFDS-001-SAFE-005 — Forbidden sequences**  
Known unsafe command sequences or resource combinations shall be represented in driver or bench contracts and enforced where technically possible. Non-enforceable restrictions shall be marked as operator controls.

**RFDS-001-SAFE-006 — Operator actions**  
Operations requiring manual confirmation, physical reconfiguration, protective equipment, or visual inspection shall be explicit and shall not be silently automated.

**RFDS-001-SAFE-007 — Emergency handling**  
B1 bench projects shall define an emergency shutdown sequence that does not depend on successful completion of the normal test flow.

---

## 27. Resource and Concurrency Model

**RFDS-001-RES-001 — Resource declaration**  
Each driver and bench contract shall identify relevant resources, including communication sessions, ports, addresses, USB devices, buses, SDK handles, power rails, channels, fixtures, relays, measurement paths, DUT interfaces, and files requiring controlled access.

**RFDS-001-RES-002 — Resource access mode**  
Each resource shall be classified as one of:

- exclusive;
- shareable;
- read-only shareable;
- multiplexed;
- externally locked;
- unsafe for parallel operation.

**RFDS-001-RES-003 — Default concurrency policy**  
Concurrency shall be disabled by default when the device, protocol, transport, or driver is not proven safe for concurrent access.

---

## 28. Configuration Requirements

**RFDS-001-CFG-001 — Configuration model**  
Configuration shall:

- separate reusable driver defaults from bench-specific values;
- support declared files, environment variables, or constructor arguments;
- document precedence when multiple sources are allowed;
- validate required fields;
- avoid embedding credentials in source or reports;
- permit deterministic export of effective configuration with secrets redacted;
- identify units explicitly;
- preserve backwards-compatible field names unless a controlled migration is approved.

**RFDS-001-CFG-002 — Portable examples**  
A released example shall not depend on an undocumented local path, developer-specific device identifier, or hidden environment state.

---

## 29. Logging and Evidence Requirements

**RFDS-001-LOG-001 — Operational logging**  
Drivers shall log enough information to diagnose connection attempts, transport-profile selection, state transitions, protocol failures, timeouts, retries, recovery, device-reported errors, cancellation, and cleanup results.

**RFDS-001-LOG-002 — Secret handling**  
Logs and evidence shall redact passwords, tokens, credentials, private keys, and other secrets.

**RFDS-001-LOG-003 — Version evidence**  
Applicable test runs shall record:

- driver package version;
- API version;
- Python version;
- Robot Framework version;
- operating system;
- transport profile;
- simulator version or device identity;
- device firmware version when available;
- test-suite or conformance version;
- exact RFDS compliance baseline;
- effective configuration with secrets redacted.

**RFDS-001-LOG-004 — Trace correlation**  
Protocol traces shall identify the keyword, protocol vector, test case, timestamp, and session that produced each exchange.

**RFDS-001-LOG-005 — Evidence retention**  
Release evidence shall be stored in a reproducible directory structure and referenced by the release manifest and release review.

RFDS-008 is the sole normative source for the complete logging, evidence, and diagnostic-bundle schema (event envelopes, evidence manifest, measurement CSV/JSONL, redaction, and integrity rules); the requirements above are platform-level minimums only and shall be read as consistent with RFDS-008.

---

## 30. Documentation Requirements

**RFDS-001-DOC-001 — Required documentation topics**  
Each P1 release shall provide current documentation for:

- supported devices and variants;
- supported transports;
- installation;
- Python environment setup;
- PyCharm setup;
- Robot Framework setup;
- connection examples;
- keyword reference;
- configuration;
- common workflows;
- state ownership and cancellation;
- safety;
- errors and troubleshooting;
- simulator use where available;
- test and conformance execution;
- package version and change history;
- known limitations;
- migration and deprecation notes.

**RFDS-001-DOC-002 — Documentation consistency**  
README, guides, GitHub Pages content, examples, AI contract, Libdoc output, release manifest, and public API shall not contradict one another.

**RFDS-001-DOC-003 — Generated documentation validation**  
Generated keyword documentation shall be built from the released library or verified against it. Stale generated output shall fail documentation review.

**RFDS-001-DOC-004 — Link and version checks**  
P1 and B1 releases shall validate internal documentation links and confirm that visible release versions match the authoritative release manifest.

---

## 31. Example Requirements

**RFDS-001-EX-001 — Example count**  
A P1 driver package shall provide at least ten useful examples unless an approved scope exception documents why ten distinct examples are not possible.

**RFDS-001-EX-002 — Example quality**  
Each example shall have a distinct objective and define:

- example identifier;
- purpose;
- prerequisites;
- simulator or hardware profile;
- execution command or script;
- expected result;
- safe teardown;
- supported driver release;
- whether operator action is required.

**RFDS-001-EX-003 — Example manifest**  
The example set shall provide `examples/index.yaml` or an equivalent machine-readable manifest. Example:

```yaml
examples:
  - id: EX-001
    file: 01_connect_and_identity.robot
    purpose: Verify connection and identity
    profile: simulator
    expected_result: PASS
    safe_teardown: Disconnect
```

**RFDS-001-EX-004 — Public API use**  
Examples shall use supported public APIs unless explicitly marked as developer diagnostics.

**RFDS-001-EX-005 — Example validation**  
Each P1 example shall have a recorded execution result or an approved hardware-availability disposition for the released revision.

---

## 32. Development Lifecycle

**RFDS-001-LIFE-001 — Phase-and-gate lifecycle**  
Driver implementation shall follow RFDS-020 — Driver Implementation Lifecycle.

Each phase contains five gates:

1. **Gate 1 — Architecture and Skeleton**
2. **Gate 2 — Core Implementation**
3. **Gate 3 — Extended Features**
4. **Gate 4 — Tests and Documentation**
5. **Gate 5 — Review and Release**

A gate shall be completed and reviewed before the next gate is accepted.

**RFDS-001-LIFE-002 — Gate review dimensions**  
Each gate shall include applicable:

- functional review;
- architecture review;
- Robot Framework API review;
- documentation review;
- code-quality review.

Each completed phase shall additionally update implementation, tests, documentation, examples, AI Driver Contract, history, review evidence, and package metadata.

---

## 33. Review and Deviation Model

### 33.1 Review dimensions

**RFDS-001-REV-001 — Mandatory review dimensions**  
The `review/` folder shall contain records covering, as applicable:

- functional correctness;
- architecture and layering;
- public Robot Framework API;
- protocol mapping;
- error handling and recovery;
- state ownership and cancellation;
- safety;
- tests and evidence;
- AI contract consistency;
- documentation consistency;
- packaging and release readiness;
- backward compatibility;
- maintainability and code quality;
- dependency and supply-chain review.

### 33.2 Severity model

**RFDS-001-REV-002 — Finding severity**  
Review findings shall use at least:

- Critical;
- Major;
- Minor;
- Observation.

### 33.3 Release blocking rules

**RFDS-001-REV-003 — Finding disposition**

- unresolved Critical findings shall block every release class above D0;
- unresolved Major findings shall block P1 and B1 unless an exceptional, time-limited deviation is approved;
- Minor findings shall have an owner and disposition;
- Observations may be recorded without corrective action.

### 33.4 Deviation record

**RFDS-001-DEV-001 — Formal deviation schema**  
Every deviation shall record equivalent information to:

```yaml
deviation_id: DEV-2026-004
requirement_id: RFDS-001-TEST-004
severity: Major
reason: Real hardware unavailable
risk: Protocol verified only using simulator
scope: Release 26.05
owner: Driver maintainer
approved_by: Release authority
approval_date: 2026-07-26
expiry_date: 2026-09-30
required_follow_up: Complete real-device validation
status: OPEN
```

**RFDS-001-DEV-002 — Deviation constraints**

- Critical findings shall not be waived for P1 or B1 release;
- Major deviations shall be exceptional, scoped, and time-limited;
- an expired deviation shall fail release acceptance;
- a deviation shall not silently transfer to a newer release;
- the release manifest shall list all active deviation identifiers.

---

## 34. Versioning and Release Management

### 34.1 Separate version concepts

**RFDS-001-VER-001 — Version separation**  
Each release shall distinguish at least:

```yaml
release_version: "26.05"
api_version: "1.0"
ai_contract_schema_version: "3.0"
protocol_vector_schema_version: "1.1"
```

A package release update does not automatically imply an API version change.

### 34.2 Authoritative version source

**RFDS-001-VER-002 — Single release-version authority**  
The release version shall have one authoritative source and shall be exposed consistently through package metadata, Python module metadata, README, AI contract, history, release notes, generated documentation, and test evidence.

### 34.3 Change classification

**RFDS-001-VER-003 — Change categories**  
Each release shall classify changes as applicable:

- added;
- changed;
- fixed;
- deprecated;
- removed;
- security;
- documentation;
- test or conformance;
- packaging.

### 34.4 Breaking changes

**RFDS-001-VER-004 — Breaking-change control**  
A breaking public API or behaviour change requires:

- explicit approval;
- an incremented API major version;
- migration guidance;
- affected keyword and schema inventory;
- updated AI contract;
- updated protocol vectors;
- updated examples and tests;
- release-note warning;
- compatibility decision documented in review.

### 34.5 Reproducibility

**RFDS-001-VER-005 — Reproducible release relationship**  
A release package shall be buildable from its declared source and dependency metadata or shall document unavoidable external build inputs and their versions.

---

## 35. Compatibility Requirements

**RFDS-001-COMP-001 — Compatibility surface**  
Compatibility shall be assessed for:

- Robot Framework keyword names;
- aliases;
- argument order and defaults;
- accepted value formats;
- return types and schemas;
- error categories and codes;
- configuration keys;
- AI contract capability identifiers;
- protocol behaviour;
- package import paths;
- scripts and documented commands.

**RFDS-001-COMP-002 — Compatibility report**  
P1 and B1 releases shall provide `release/compatibility_report.json` or an equivalent machine-readable record containing the prior release compared, changed surfaces, compatibility verdict, and migration requirement.

---

## 36. Security and Supply-Chain Requirements

**RFDS-001-SEC-001 — Secure project handling**  
Drivers and supporting scripts shall:

- avoid storing plaintext credentials in source control;
- redact secrets from logs and evidence;
- validate file paths and external inputs where applicable;
- avoid executing untrusted shell content;
- use secure transport options when supported and required;
- document insecure legacy protocols;
- constrain firmware update, file upload, reset, or destructive operations;
- avoid unsafe deserialization of untrusted data.

**RFDS-001-SEC-002 — Dependency evidence**  
P1 and B1 releases shall identify:

- direct runtime dependencies and versions;
- relevant development and test dependencies;
- licences;
- vendored source or binaries;
- required external SDKs and installers;
- vulnerability-review status;
- unresolved supply-chain risks.

**RFDS-001-SEC-003 — Binary provenance**  
A release shall not contain undocumented binary dependencies or executables.

Security controls shall not be represented as product or electrical safety certification.

---

## 37. Reliability and Performance Requirements

**RFDS-001-REL-001 — Failure behaviour**  
A driver shall define behaviour for applicable invalid arguments, unavailable device, connection loss, timeout, partial response, malformed response, device error code, stale session, unsupported command, cleanup failure, and interrupted execution.

**RFDS-001-REL-002 — Recovery semantics**  
Recovery may include retry, buffer clearing, reconnection, session recreation, device error clearing, or safe shutdown. The original failed operation shall remain visible even when recovery succeeds.

**RFDS-001-PERF-001 — Device-specific performance contract**  
Each driver shall document, where applicable:

- expected connection time;
- normal keyword latency;
- stabilization delay;
- maximum operation timeout;
- retry count and backoff;
- acquisition throughput;
- polling interval;
- cancellation latency;
- concurrency limitations;
- known slow operations.

Performance optimization shall not bypass validation, safety, required settling, or protocol-integrity checks.

---

## 38. GitHub Repository and Publication Requirements

**RFDS-001-GH-001 — Repository completeness**  
A P1 or B1 repository shall include current README, licence, installation metadata, source code, tests, examples, scripts, guides, history, reviews, AI contract, documentation source, GitHub Pages content or build configuration, release notes, and contribution guidance required by project policy.

**RFDS-001-GH-002 — Published documentation revision**  
GitHub Pages shall reflect the released API and revision. Stale generated API pages shall fail documentation review.

---

## 39. Platform Acceptance Criteria

A release satisfies RFDS-001 only when all requirements mandatory for its release class have an accepted disposition.

### 39.1 Mandatory P1 acceptance

**RFDS-001-ACC-001 — P1 production acceptance**  
A P1 driver shall satisfy all of the following:

1. the release ZIP name and stable internal root pass automated validation;
2. `release_manifest.yaml` exists and matches package contents;
3. all mandatory package paths and artifacts exist;
4. the library imports and Libdoc generation succeeds;
5. 100% of exported public keywords are inventoried;
6. public keyword signatures, return schemas, errors, state, timeout, and cancellation requirements are documented;
7. device-facing keywords map to explicit protocol operations or approved exclusions;
8. all blocking operations have finite timeout or documented interruptibility;
9. applicable safe initialization, teardown, limits, emergency behaviour, and recovery are implemented and tested;
10. the RFDS-017 AI Driver Contract and lock match the released API and keyword inventory;
11. RFDS-019 conformance passes for all mandatory vectors;
12. representative real-device validation passes;
13. every example in `examples/index.yaml` has an accepted execution disposition;
14. README, guide, GitHub Pages, AI contract, Libdoc, manifest, and code pass consistency checks;
15. version information is consistent across release artifacts;
16. all mandatory CI or local validation jobs pass;
17. no unresolved Critical finding exists;
18. no unresolved Major finding exists unless covered by a valid exceptional deviation;
19. changes are recorded in `history/` and release notes;
20. dependency inventory, SBOM, checksums, compatibility report, and traceability records exist;
21. clean-environment installation and the declared basic workflow are reproduced successfully;
22. no required item remains `NOT_RUN`.

### 39.2 Mandatory B1 acceptance

**RFDS-001-ACC-002 — B1 bench acceptance**  
A B1 release shall meet applicable P1 requirements for included drivers and shall additionally provide:

- an RFDS-018 system contract;
- verified topology and resource declarations;
- global safety and emergency shutdown workflow;
- multi-driver setup, execution, recovery, and teardown evidence;
- bench-level requirement and capability traceability.

---

## 40. Failure Conditions

**RFDS-001-FAIL-001 — Platform review failure**  
A release shall fail RFDS-001 review when any mandatory condition applies, including:

- release structure or internal root is incorrect;
- release manifest is missing, invalid, or inconsistent;
- a required folder or release artifact is missing;
- the library cannot be imported by Robot Framework;
- public keywords are undocumented or accidentally exported;
- a public device-facing keyword has no defined protocol intent or approved exclusion;
- blocking communication can remain unbounded without approved interruptibility;
- the driver reports success after a required protocol failure;
- required cancellation or safe teardown behaviour is absent;
- AI contract data contradicts the released API;
- public keywords are omitted from conformance inventory without approval;
- examples use unsupported or private APIs;
- README, guides, GitHub Pages, Libdoc, or manifest describe a different revision;
- required tests, reviews, checksums, SBOM, compatibility evidence, or traceability evidence are missing;
- unresolved Critical findings remain;
- a Major deviation is expired or unapproved;
- an undocumented breaking change is introduced;
- secrets are included in release files or evidence;
- undocumented binaries or dependencies are present;
- a required item remains `NOT_RUN`.

---

## 41. Minimum Definition of Done

**RFDS-001-DOD-001 — Driver completion**  
RFDS-001 is implemented for a release when:

- the selected release class is declared;
- all applicable requirements have a disposition;
- the driver follows the layered architecture or an approved equivalent;
- the package and repository meet mandatory structure and content requirements;
- the public Robot Framework API is stable, documented, discoverable, and explicitly exported;
- transport and protocol behaviour is explicit and testable;
- AI Driver Contract files are complete and synchronized;
- bench integration information is available where applicable;
- call and protocol conformance evidence is generated;
- safety, state ownership, cancellation, configuration, logging, timeout, and recovery policies are implemented at the responsible layer;
- required examples, scripts, guides, README, GitHub Pages, history, reviews, manifest, integrity records, and traceability records are present;
- lifecycle gates and release reviews are complete;
- all release-class acceptance criteria pass.

---

## 42. Review Checklist

1. Is the release class declared?
2. Is the exact RFDS compliance baseline recorded?
3. Does the driver fit the RFDS layered architecture?
4. Is the public Robot Framework API separated from protocol and transport details?
5. Are canonical lifecycle keywords used where supported?
6. Are connection, state ownership, timeout, cancellation, error, and recovery behaviours explicit?
7. Is the release package named correctly?
8. Does the ZIP contain the stable `rf_<driver_name>/` root?
9. Are all mandatory folders, manifest files, and integrity records present?
10. Are at least ten useful examples provided or is an exception approved?
11. Does every example have a manifest entry, execution command, expected result, and safe teardown?
12. Are README, guides, Libdoc, and GitHub Pages current?
13. Is the AI Driver Contract complete, locked, and synchronized?
14. Is bench integration represented through RFDS-018 where applicable?
15. Are all exported keywords inventoried and tested through RFDS-019?
16. Is outbound and inbound protocol behaviour observable?
17. Is the simulator profile versioned and its fidelity declared?
18. Are safety limits, emergency actions, and teardown behaviour defined?
19. Are shared and exclusive resources declared?
20. Are configuration and secrets handled correctly?
21. Are release and API versions independently controlled?
22. Is compatibility against the prior release recorded?
23. Are changes documented in history and release notes?
24. Are mandatory reviews and CI validations present?
25. Are dependency, licence, SBOM, checksum, and binary-provenance records present?
26. Are all Critical findings closed?
27. Are all Major findings closed or covered by a valid exceptional deviation?
28. Does every applicable requirement have an accepted disposition?
29. Does the clean-environment installation test pass?
30. Does the complete release satisfy the selected class acceptance criteria?

---

## 43. Goal

Create a unified, safe, testable, AI-readable, and production-oriented Robot Framework driver platform in which every released driver has a consistent architecture, stable public API, explicit device protocol behaviour, traceable validation evidence, controlled compatibility, and complete release documentation.

---

## Appendix A — Reference Architecture Diagram

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Test requirements, operator intent, and bench safety constraints     │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                 ┌──────────────▼──────────────┐
                 │ Human designer or AI planner│
                 │ RFDS-017 + RFDS-018         │
                 └──────────────┬──────────────┘
                                │
                 ┌──────────────▼──────────────┐
                 │ Robot Framework suites      │
                 │ resources and orchestration │
                 └──────────────┬──────────────┘
                                │ public keywords
                 ┌──────────────▼──────────────┐
                 │ Robot Framework API layer   │
                 └──────────────┬──────────────┘
                                │ semantic calls
                 ┌──────────────▼──────────────┐
                 │ Driver core / device model  │
                 └──────────────┬──────────────┘
                                │ protocol intent
                 ┌──────────────▼──────────────┐
                 │ Protocol adapter            │
                 └──────────────┬──────────────┘
                                │ bytes, text, request, SDK call
                 ┌──────────────▼──────────────┐
                 │ Transport boundary          │◄──── trace / spy / proxy
                 └──────────────┬──────────────┘
                                │
                 ┌──────────────▼──────────────┐
                 │ Device or approved simulator│
                 └──────────────┬──────────────┘
                                │ response / acknowledgement / fault
                 ┌──────────────▼──────────────┐
                 │ Parsing, typed result, error│
                 └──────────────┬──────────────┘
                                │
                 ┌──────────────▼──────────────┐
                 │ Robot result and evidence   │
                 │ RFDS-019 coverage and traces│
                 └─────────────────────────────┘
```

---

## Appendix B — Minimum P1 Release Tree

```text
rf_<driver_name>_v<YY>.<RR>.zip
└── rf_<driver_name>/
    ├── README.md
    ├── LICENSE
    ├── pyproject.toml
    ├── rf_<driver_name>/
    ├── ai/
    │   ├── ai_contract.yaml
    │   └── ai_contract.lock
    ├── tests/
    │   ├── unit/
    │   ├── integration/
    │   └── conformance/
    ├── examples/
    │   └── index.yaml
    ├── scripts/
    ├── guide/
    ├── docs/
    ├── site/ or buildable GitHub Pages source
    ├── history/
    ├── review/
    └── release/
        ├── release_manifest.yaml
        ├── requirements_traceability.csv
        ├── compatibility_report.json
        ├── checksums.sha256
        └── sbom.json
```

---

## Appendix C — Example Requirement Traceability Record

```csv
requirement_id,applicability,implementation,verification,result,evidence,deviation_id
RFDS-001-API-001,P1,src/rf_example/library.py,tests/conformance/import.robot,PASS,results/log.html,
RFDS-001-IO-002,P1,src/rf_example/transport/tcp.py,tests/unit/test_timeout.py,PASS,results/unit.xml,
RFDS-001-SAFE-003,P1,src/rf_example/driver.py,tests/integration/safe_teardown.robot,PASS,results/report.html,
```

---

## Appendix D — Change Record

### Version 1.1

Review-driven revision of RFDS-001 only. Major changes:

- added permanent requirement identifiers;
- added document hierarchy, subject ownership, and exact compliance baselines;
- added release classes D0, D1, D2, P1, and B1 with applicability rules;
- clarified production and gate package naming using `vYY.RR` and gate suffixes;
- separated release version, API version, AI contract schema version, and protocol-vector schema version;
- added fixed mandatory package paths and controlled alternative-path mapping;
- added authoritative release manifest, checksums, traceability, compatibility report, and SBOM requirements;
- added canonical common Robot Framework lifecycle keyword names;
- strengthened explicit keyword export, error identity, state ownership, cancellation, and recovery requirements;
- defined simulator approval and fidelity declarations;
- converted production-critical testing and regression requirements to mandatory language;
- added baseline CI and clean-environment validation requirements;
- added formal deviation governance and release-blocking rules;
- strengthened documentation, examples, supply-chain, compatibility, and measurable acceptance criteria.

### Version 1.0

Initial RFDS-001 platform specification defining:

- overall project goals;
- platform architecture and layers;
- canonical package and repository model;
- public Robot Framework API principles;
- Python, protocol, and transport requirements;
- RFDS-017, RFDS-018, and RFDS-019 integration;
- lifecycle, safety, testing, evidence, documentation, review, and release requirements;
- platform acceptance criteria and minimum definition of done.
