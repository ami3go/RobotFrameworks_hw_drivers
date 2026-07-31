# RFDS-009 — Testing Standard

## Unit Tests, Simulation, Hardware-in-the-Loop, and Robot Framework Tests

**Version:** 1.0  
**Document ID:** RFDS-009  
**Status:** Draft project requirement  
**Applies to:** All RFDS Robot Framework driver projects, shared driver-platform components, protocol simulators, test benches, examples, validation suites, and release packages

---

## 1. Purpose

This specification defines the mandatory testing strategy for the RFDS Robot Framework Driver Platform.

It establishes how each driver shall be verified from isolated Python logic through deterministic protocol simulation, Robot Framework acceptance testing, real-device hardware-in-the-loop testing, regression testing, and release evidence.

The standard shall provide objective evidence that a driver:

1. implements its declared behaviour correctly;
2. exposes a usable and stable Robot Framework API;
3. serializes and parses device protocol operations correctly;
4. handles errors, timeouts, state changes, and recovery deterministically;
5. behaves correctly against an approved simulator or protocol replay environment;
6. behaves safely and correctly against representative physical hardware where applicable;
7. preserves corrected defects through regression tests;
8. generates repeatable, traceable, and reviewable test evidence;
9. does not represent simulation as proof of physical properties that were not measured;
10. satisfies the test gates required for the applicable lifecycle stage and release status.

RFDS-009 defines the **overall driver testing standard**. RFDS-019 remains the authoritative specification for exhaustive public Robot Framework keyword callability and driver-to-device protocol conformance.

---

## 2. Scope Boundary

### 2.1 In scope

RFDS-009 covers:

- static test and packaging checks relevant to test execution;
- Python unit testing;
- protocol serialization and response-parsing tests;
- transport-adapter tests;
- deterministic protocol replay;
- approved simulator testing;
- Python integration testing;
- Robot Framework software-only acceptance testing;
- Robot Framework compatibility and regression testing;
- RFDS-019 conformance integration;
- hardware-in-the-loop testing;
- representative physical-function verification;
- safety, fault, timeout, recovery, and cleanup testing;
- performance, stress, soak, resource-leak, and concurrency testing where applicable;
- test data, fixtures, simulators, resource profiles, tagging, and execution control;
- code-coverage requirements;
- test result classification;
- test evidence and traceability;
- CI, manually approved HIL workflows, and release test gates;
- handling of skipped, excluded, quarantined, flaky, and not-run tests;
- requirements for regression tests after defect correction.

### 2.2 Out of scope

RFDS-009 does not define:

- the complete device-specific feature set;
- vendor-specific protocol syntax;
- the public keyword naming standard;
- the complete package layout outside test-related paths;
- the project-wide logging schema;
- the complete exception hierarchy;
- calibration procedures unless the device-specific task requires them;
- universal electrical accuracy limits;
- universal performance limits for every device type;
- laboratory accreditation or safety certification;
- production test limits for a specific DUT;
- the complete RFDS-019 protocol-vector schema.

These matters shall be defined by the applicable RFDS specification, device-specific implementation task, AI Driver Contract, AI Test Bench Contract, vendor documentation, bench procedure, or approved validation plan.

---

## 3. Normative References

A project conforming to RFDS-009 shall also apply the relevant requirements from:

- **RFDS-001 — Platform Requirements**;
- **RFDS-002 — Mandatory Public API and Robot Framework Keyword Standard**;
- **RFDS-003 — BaseInstrumentLibrary**;
- **RFDS-004 — Transport Layer Specification**;
- **RFDS-005 — Driver Package Specification**;
- **RFDS-006 — Coding Standard**;
- **RFDS-007 — Error and Exception Standard**;
- **RFDS-008 — Logging and Evidence Standard**;
- **RFDS-010 — Review Checklist**, when approved;
- **RFDS-011 — Release Process**, when approved;
- **RFDS-017 — AI Driver Contract Specification**;
- **RFDS-018 — AI Test Bench Contract Specification**;
- **RFDS-019 — Robot Framework Driver Call and Protocol Conformance Test Specification**;
- **RFDS-020 — Driver Implementation Lifecycle**;
- the device-specific implementation requirements;
- applicable vendor protocol and hardware documentation.

When requirements conflict, safety requirements shall take precedence. Unresolved conflicts shall be recorded and reviewed rather than silently interpreted.

---

## 4. Normative Terminology

- **shall / shall not** — mandatory requirement;
- **should / should not** — recommended requirement; deviation requires documented justification;
- **may** — permitted implementation choice;
- **test layer** — a category of tests defined by execution boundary and evidence objective;
- **software-only test** — a test that requires no uncontrolled physical hardware;
- **unit test** — a test of a small Python unit with dependencies isolated at an appropriate boundary;
- **integration test** — a test of multiple real project components operating together;
- **simulator** — a deterministic implementation of the device-facing protocol boundary;
- **protocol replay** — deterministic reproduction of recorded or authored device responses and fault sequences;
- **Robot acceptance test** — a Robot Framework test that validates user-visible behaviour through public keywords;
- **HIL test** — a test that communicates with real physical hardware;
- **representative hardware test** — a selected physical-device test that proves a declared behaviour or integration path without necessarily testing every parameter combination;
- **oracle** — an explicit rule used to determine PASS or FAIL;
- **fixture** — controlled test setup, dependency, bench resource, data file, or helper used by a test;
- **test profile** — a declared configuration selecting simulator, replay, real hardware, safety limits, resources, and execution rules;
- **mandatory test** — a test required for the applicable scope and release status;
- **excluded test** — a test formally declared not applicable or prohibited, with an approved reason;
- **quarantined test** — a known unstable or defective test isolated from normal execution under controlled review;
- **flaky test** — a test that produces inconsistent results without an intentional change in inputs or environment;
- **release evidence** — retained test outputs used to support a gate or release decision.

---

## 5. Testing Principles

### 5.1 Test at the lowest effective layer

A behaviour shall be tested at the lowest layer that can prove it accurately and deterministically.

Examples:

- numeric conversion shall be tested in Python unit tests;
- protocol formatting shall be tested at the protocol adapter boundary;
- public keyword argument conversion shall be tested through Robot Framework;
- physical output behaviour shall be tested on real hardware;
- a fixed user-visible defect should receive both a low-layer regression test and a Robot-level regression test when practical.

### 5.2 Use multiple independent evidence types

No single test category shall be treated as complete proof of production readiness.

In particular:

- unit-test coverage does not prove protocol correctness;
- simulator success does not prove physical performance;
- HIL success does not replace deterministic software-only regression coverage;
- a Robot suite that returns without error does not prove the correct protocol operation was transmitted;
- RFDS-019 conformance does not prove electrical accuracy, calibration, stress tolerance, or complete release readiness.

### 5.3 Determinism

Software-only tests shall be deterministic.

They shall control or replace as applicable:

- time;
- random values;
- network availability;
- device responses;
- thread scheduling assumptions;
- temporary paths;
- environment variables;
- locale;
- transport timing;
- process-global state.

Randomized or property-based tests shall record the seed required to reproduce a failure.

### 5.4 Isolation

Tests shall not depend on undocumented execution order or residue from a previous test.

Each test shall declare its prerequisites and establish or verify the required starting state.

### 5.5 Finite execution

Every test involving communication, waiting, retry, polling, acquisition, thread synchronization, process execution, or external resources shall have a finite timeout.

### 5.6 Explicit oracles

A test shall not pass only because no exception occurred.

Each test shall verify one or more explicit outcomes such as:

- return value;
- return type;
- exception type;
- failure message;
- state transition;
- protocol command;
- raw response;
- device status;
- physical measurement;
- timing limit;
- cleanup state;
- evidence file content.

### 5.7 Safe teardown

Tests that can change device, fixture, or DUT state shall define cleanup that executes after PASS, FAIL, timeout, and interruption as far as the environment permits.

### 5.8 Traceability

Every test required by a specification or implementation task shall have a stable identifier or a documented mapping to the applicable requirement.

### 5.9 Truthful qualification status

A project shall distinguish clearly between:

- software-only validated;
- simulator validated;
- protocol-conformant;
- representative hardware validated;
- fully HIL-qualified for a declared profile;
- not yet hardware validated.

A more advanced status shall not be claimed without corresponding evidence.

---

## 6. Test-Layer Model

A production driver shall use the following layers as applicable:

| Level | Test layer | Primary objective | Hardware required |
|---|---|---|---|
| T0 | Static and package checks | Verify importability, syntax, structure, metadata, generated API, and test discoverability | No |
| T1 | Python unit tests | Verify isolated logic, validation, conversion, state, exceptions, and command construction | No |
| T2 | Protocol and transport component tests | Verify serialization, parsing, framing, checksums, timeouts, retry, and adapter contracts | No |
| T3 | Replay and simulator integration | Verify complete deterministic driver behaviour at the real protocol boundary | No |
| T4 | Robot Framework software acceptance | Verify public-keyword behaviour through Robot Framework | No |
| T5 | RFDS-019 conformance | Verify public keyword callability and observed protocol exchange | Simulator and/or hardware |
| T6 | Representative HIL | Verify connection and declared behaviour on real supported devices | Yes |
| T7 | Physical function and accuracy tests | Verify device output, measurement, timing, or other physical properties | Yes, often with reference equipment |
| T8 | Performance, stress, soak, recovery, and concurrency | Verify long-duration and demanding operational behaviour | Depends on scope |
| T9 | Release regression | Re-run the approved release matrix and preserve evidence | Depends on matrix |

A project may add device-specific layers, but it shall not weaken or silently omit applicable layers.

---

## 7. Mandatory Test Directory Structure

Each project shall provide the following test structure, directly or through an approved equivalent:

```text
rf_<driver_name>/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── robot/
│   ├── compatibility/
│   ├── replay/
│   ├── conformance/
│   ├── hil/
│   ├── performance/
│   ├── support/
│   └── data/
├── config/
│   └── hil_resources.example.yaml
├── scripts/
│   ├── run_tests.bat
│   ├── run_tests.ps1
│   ├── run_tests.sh
│   ├── run_hil_tests.bat
│   ├── run_hil_tests.ps1
│   └── run_hil_tests.sh
└── results/
    └── .gitkeep
```

### 7.1 `tests/unit/`

Contains pure Python tests for:

- converters;
- parsers;
- validators;
- state machines;
- error mapping;
- command builders;
- configuration processing;
- retry and timeout policy;
- safety limits;
- session ownership;
- result models;
- diagnostics helpers;
- other isolated production logic.

### 7.2 `tests/integration/`

Contains tests of multiple real project components together, such as:

- library to core delegation;
- core to protocol adapter;
- protocol adapter to simulator transport;
- configuration to session creation;
- error propagation through multiple layers;
- reconnect and recovery workflows;
- diagnostic bundle generation.

### 7.3 `tests/robot/`

Contains Robot Framework acceptance and regression suites that use the public library API.

Software-only Robot suites shall normally use an approved simulator, fake device service, or protocol replay profile.

### 7.4 `tests/compatibility/`

Contains tests for:

- supported Python versions;
- supported Robot Framework versions;
- supported dependency versions or ranges;
- public API compatibility;
- aliases and deprecations;
- configuration-schema compatibility;
- compatibility with supported device models or firmware where deterministic evidence is available.

### 7.5 `tests/replay/`

Contains deterministic protocol captures, authored response sequences, replay tests, and golden data.

### 7.6 `tests/conformance/`

Contains RFDS-019 keyword inventory, protocol vectors, Robot conformance suites, response schemas, and exclusion records.

### 7.7 `tests/hil/`

Contains explicitly enabled real-device tests.

### 7.8 `tests/performance/`

Contains applicable:

- timing tests;
- throughput tests;
- stress tests;
- soak tests;
- memory and file-descriptor leak tests;
- reconnect-cycle tests;
- concurrent-session tests;
- repeated acquisition tests.

### 7.9 `tests/support/`

Contains shared:

- simulators;
- fakes;
- spies;
- fixtures;
- Robot support libraries;
- resource-locking helpers;
- test profile loaders;
- evidence helpers;
- deterministic clocks;
- protocol trace decoders.

Production code shall not import test-support modules.

### 7.10 `tests/data/`

Contains sanitized:

- protocol vectors;
- protocol captures;
- expected responses;
- configuration examples;
- input tables;
- response schemas;
- physical-test limits;
- reference measurements where approved.

Secrets, personal paths, private addresses, and uncontrolled laboratory configuration shall not be committed.

---

## 8. Test Identification and Naming

### 8.1 Stable test identifiers

Tests required for traceability shall use stable identifiers.

Recommended patterns are:

```text
UNIT-<AREA>-<NNN>
INT-<AREA>-<NNN>
ROBOT-<CAPABILITY>-<NNN>
REPLAY-<PROTOCOL>-<NNN>
CONF-<KEYWORD>-<NNN>
HIL-<CAPABILITY>-<NNN>
PERF-<AREA>-<NNN>
REG-<ISSUE_OR_REQUIREMENT>-<NNN>
```

Example:

```text
UNIT-PARSER-014
ROBOT-CONNECTION-003
HIL-DC-VOLTAGE-007
REG-ISSUE-142-001
```

### 8.2 Test names

Test names shall describe the expected behaviour rather than implementation activity.

Preferred:

```text
Connect Rejects Unsupported VISA Resource
Malformed Identity Response Raises Protocol Error
Output Is Disabled During Failed Suite Teardown
```

Not preferred:

```text
Test Connect
Test Parser 2
Check Error
```

### 8.3 Requirement metadata

A test should reference applicable identifiers through one or more of:

- pytest marker;
- docstring;
- Robot tag;
- test data field;
- requirement traceability matrix.

---

## 9. Test Profiles

Every non-trivial test run shall use a declared profile.

Recommended profile names are:

- `unit`;
- `software`;
- `simulator`;
- `replay`;
- `conformance_simulator`;
- `hil_read_only`;
- `hil_safe_output`;
- `hil_full`;
- `performance`;
- `soak`;
- `compatibility`;
- `release`.

A profile shall define as applicable:

- driver version;
- transport type;
- simulator or replay version;
- real-device resource;
- model and firmware constraints;
- allowed operations;
- prohibited operations;
- channel selection;
- safety limits;
- startup state;
- teardown state;
- timeout and retry settings;
- stabilization rules;
- fixture requirements;
- operator actions;
- resource locks;
- evidence destination;
- required environment variables;
- secrets-redaction rules.

The effective profile shall be recorded with test evidence.

---

## 10. Python Unit-Test Requirements

### 10.1 General requirements

Unit tests shall:

- execute without physical hardware;
- avoid uncontrolled network access;
- isolate external vendor SDKs unless the SDK itself is the unit under test;
- use deterministic input and output;
- run quickly enough for normal developer and CI use;
- verify success and failure paths;
- assert types, values, state, and exceptions explicitly;
- avoid over-mocking the function under test.

### 10.2 Mandatory unit-test subjects

The following shall be unit-tested where present:

1. Robot argument converters;
2. protocol command builders;
3. protocol response parsers;
4. binary framing and checksums;
5. terminator and encoding handling;
6. range and enum validation;
7. unit conversion;
8. configuration parsing and precedence;
9. state-machine transitions;
10. session lookup and ownership;
11. timeout calculation;
12. retry eligibility and backoff calculation;
13. error and exception mapping;
14. safety-limit enforcement;
15. safe-default and safe-teardown logic;
16. capability discovery;
17. diagnostics data generation;
18. version and metadata reporting;
19. API aliases and deprecation helpers;
20. all corrected deterministic defects at the lowest effective layer.

### 10.3 Boundary coverage

For each applicable validation or conversion function, tests shall cover:

- nominal value;
- minimum accepted value;
- maximum accepted value;
- immediately invalid value below minimum;
- immediately invalid value above maximum;
- wrong type;
- missing required value;
- explicit default;
- `None` handling where accepted;
- representative enum values;
- invalid enum;
- floating-point rounding or formatting boundaries where relevant.

### 10.4 Exception assertions

Unit tests shall assert the documented exception class and meaningful message content.

A broad assertion such as `raises(Exception)` is insufficient unless the behaviour under test intentionally permits multiple documented exception types.

### 10.5 State-machine tests

Stateful drivers shall test:

- valid transitions;
- invalid transitions;
- idempotent operations where declared;
- cleanup from each relevant state;
- failed transition behaviour;
- recovery transition behaviour;
- state after timeout;
- state after disconnect;
- state after partial protocol success.

### 10.6 Retry tests

Retry logic shall be tested with a deterministic clock or equivalent control.

Tests shall verify:

- retryable errors;
- non-retryable errors;
- attempt count;
- timeout budget;
- backoff calculation;
- final exception;
- no duplicate unsafe side effect where the operation is not idempotent;
- recovery after a successful later attempt.

---

## 11. Protocol Serialization and Parsing Tests

### 11.1 Outbound serialization

Every protocol operation type shall have deterministic tests for:

- command or request identity;
- argument order;
- units;
- number formatting;
- addressing;
- channel selection;
- separators;
- terminators;
- encoding;
- length fields;
- checksums or integrity fields;
- request body or payload schema;
- no-response versus response-producing semantics.

### 11.2 Inbound parsing

Every response parser shall test:

- nominal response;
- minimum valid response;
- maximum valid response;
- whitespace and terminator variants allowed by the protocol;
- malformed response;
- empty response;
- incomplete response;
- unexpected field count;
- invalid numeric value;
- invalid enum;
- device error response;
- overflow or out-of-range value;
- checksum or integrity failure where applicable;
- trailing or concatenated frames where applicable.

### 11.3 Golden vectors

Protocol tests should use reviewed golden vectors stored under `tests/data/`.

A golden vector shall identify:

- source or author;
- protocol revision;
- applicable device model or firmware;
- input arguments;
- expected outbound bytes or text;
- expected inbound bytes or text;
- expected parsed result or exception;
- normalization rules;
- approval status.

### 11.4 Independent oracle

Where practical, expected protocol data shall not be generated by the same production function being tested.

---

## 12. Transport-Adapter Tests

Each transport implementation shall have tests for its declared contract.

Tests shall cover as applicable:

- open and close;
- repeated close;
- repeated open behaviour;
- write;
- read;
- query or transaction;
- partial read;
- delayed response;
- timeout;
- connection refused;
- disconnected peer;
- invalid resource syntax;
- unsupported configuration;
- encoding and line termination;
- binary transfer;
- buffer handling;
- cleanup after open failure;
- cleanup after read or write failure;
- cancellation or interruption behaviour;
- thread or session ownership;
- trace-hook behaviour;
- secret redaction.

Transport tests may use loopback services, in-process servers, pseudo terminals, virtual CAN, fake SDKs, or other deterministic facilities.

They shall not silently depend on an uncontrolled external laboratory resource.

---

## 13. Protocol Replay Requirements

### 13.1 Purpose

Replay testing shall provide deterministic validation of real or approved protocol exchanges without requiring hardware.

### 13.2 Replay data

Replay data shall be:

- sanitized;
- versioned;
- deterministic;
- attributable to a protocol or device revision;
- protected from accidental modification by tests;
- reviewed when used as an acceptance oracle.

### 13.3 Replay scenarios

Replay shall cover as applicable:

- normal connection and identity;
- representative command acknowledgements;
- representative query responses;
- multi-frame or block responses;
- empty response;
- malformed response;
- device error queue response;
- timeout;
- disconnect;
- reconnect;
- unsupported command;
- checksum failure;
- delayed response;
- recovery after fault.

### 13.4 Replay limitations

Replay evidence shall not be described as real-device evidence.

A replay can prove deterministic handling of the recorded exchange, not the continued correctness of all supported hardware or firmware revisions.

---

## 14. Approved Simulator Requirements

### 14.1 Protocol-boundary fidelity

An approved simulator shall operate at the same device-facing boundary used by the production driver, such as:

- TCP socket;
- serial byte stream;
- VISA-compatible session boundary;
- HTTP service;
- Modbus endpoint;
- CAN frame boundary;
- vendor SDK function boundary;
- GPIO or relay SDK boundary.

Mocking only an internal driver method is not sufficient to qualify as protocol simulation when the objective is protocol behaviour.

### 14.2 Determinism

The simulator shall allow deterministic configuration of:

- responses;
- state;
- delay;
- timeout;
- malformed data;
- device error codes;
- disconnection;
- recovery;
- unsupported operations;
- model and firmware identity;
- state readback.

### 14.3 Stateful behaviour

Where the real device is stateful, the simulator should model the state required to verify:

- connection state;
- selected mode or channel;
- set/readback behaviour;
- output enable state;
- error queue;
- trigger or acquisition state;
- reset and clear operations;
- safe teardown.

The simulator shall not claim physical fidelity beyond its declared model.

### 14.4 Simulator validation

The simulator itself shall have tests proving:

- command recognition;
- expected response generation;
- state transitions;
- fault injection;
- trace recording;
- reset between tests;
- deterministic timing behaviour;
- no leakage of state between sessions unless intentionally modeled.

### 14.5 Simulator identity

Every simulator run shall record:

- simulator name;
- simulator version;
- protocol profile;
- modeled device identity;
- modeled firmware revision;
- enabled fault mode;
- scenario or vector identifier.

### 14.6 Simulator limitations file

The project shall document simulator limitations, including behaviours not modeled and physical properties that cannot be validated.

---

## 15. Python Integration Tests

Integration tests shall verify component interaction without relying on uncontrolled hardware.

They shall cover as applicable:

- library initialization without hardware access;
- public adapter to core delegation;
- core to transport interaction;
- configuration to transport construction;
- named-session creation and lookup;
- multiple independent sessions;
- capability reporting;
- diagnostics export;
- error propagation across layers;
- timeout propagation;
- reconnect workflow;
- safe cleanup after partial initialization;
- simulator-backed end-to-end Python calls;
- package installation and import from a clean environment.

An integration test shall use real project components except for the external boundary intentionally replaced by a simulator, fake service, or controlled SDK spy.

---

## 16. Robot Framework Software Acceptance Tests

### 16.1 Purpose

Robot acceptance tests shall verify the driver through the same public Robot Framework interface used by users and AI-generated test plans.

### 16.2 Mandatory subjects

Robot tests shall cover as applicable:

1. library import;
2. Libdoc-visible keyword availability;
3. connection and identity;
4. basic device configuration;
5. representative write or set operation;
6. representative query or read operation;
7. return-value type and schema;
8. assertion or verification keyword;
9. state precondition failure;
10. invalid argument failure;
11. timeout failure;
12. protocol or device error failure;
13. reconnect or recovery;
14. safe disconnect;
15. suite-teardown cleanup;
16. configuration loading;
17. named sessions where supported;
18. multiple channels or resources where supported;
19. diagnostics or evidence export;
20. corrected user-visible defects.

### 16.3 Public API only

Robot acceptance tests shall use public keywords except where a test is explicitly labeled as an internal developer diagnostic.

### 16.4 Robot argument conversion

Tests shall verify:

- positional arguments;
- named arguments where supported;
- omitted optional arguments;
- explicit defaults;
- Robot scalar/list/dictionary conversion;
- numeric-string conversion;
- boolean conversion;
- enum and unit conversion;
- invalid Robot argument failure;
- returned Robot-compatible values.

### 16.5 Setup and teardown

Suites shall use explicit setup and teardown.

A test shall not depend on a previous test having connected, selected a channel, cleared an error, or established a safe state unless the dependency is declared and controlled within the suite architecture.

### 16.6 Simulator-backed execution

Software-only Robot suites shall run against the approved simulator or replay profile in CI.

They shall not silently connect to local hardware.

### 16.7 Robot result files

Every Robot execution used as evidence shall preserve:

- `output.xml`;
- `log.html`;
- `report.html`.

---

## 17. RFDS-019 Conformance Integration

RFDS-019 testing is a mandatory specialized layer for released public drivers.

RFDS-009 shall treat RFDS-019 as the authoritative source for:

- public keyword inventory;
- keyword callability;
- protocol-vector coverage;
- observed outbound protocol verification;
- observed inbound response verification;
- parsed Robot return verification;
- protocol error and recovery vectors;
- conformance statuses and evidence.

RFDS-009 adds the broader context of unit, integration, simulator, HIL, performance, regression, CI, and release testing.

A project shall not duplicate or weaken RFDS-019 acceptance rules inside an alternative test suite.

---

## 18. Hardware-in-the-Loop Requirements

### 18.1 Explicit enablement

HIL tests shall be disabled by default.

Execution shall require an explicit enable flag such as:

```text
--variable HIL_ENABLED:true
```

or an approved equivalent.

The HIL runner shall reject execution when mandatory safety or resource variables are missing.

### 18.2 No silent fallback

When a HIL profile is selected, failure to connect to real hardware shall not silently fall back to simulation.

The result shall be FAIL or approved SKIP according to the declared prerequisite policy.

### 18.3 HIL resource profile

A real-device test profile shall define as applicable:

- device model or family;
- supported firmware range;
- serial number or approved selection rule;
- transport and resource address;
- fixture identity;
- connected reference equipment;
- channel mapping;
- allowed operations;
- prohibited operations;
- voltage, current, power, temperature, resistance, speed, pressure, relay, or other limits;
- startup state;
- shutdown state;
- emergency shutdown sequence;
- operator actions;
- stabilization delays;
- calibration prerequisites;
- exclusive resource locks;
- expected identity response;
- evidence location.

### 18.4 HIL levels

The project should distinguish at least:

- **read-only HIL** — identity, status, health, query, and diagnostics without changing hazardous outputs;
- **safe-output HIL** — controlled output or actuation within conservative limits;
- **full HIL** — the complete approved hardware validation profile;
- **destructive or exceptional HIL** — tests requiring special authorization, sacrificial hardware, or elevated risk controls.

### 18.5 Representative device coverage

For each supported device family, HIL shall verify representative operations for each applicable capability or protocol class.

A single identity query is insufficient to claim full hardware qualification.

### 18.6 Hardware identity

HIL evidence shall record, when available:

- manufacturer;
- model;
- serial number;
- firmware version;
- installed options or modules;
- transport resource;
- fixture identity;
- reference-instrument identity;
- calibration status relevant to the test.

### 18.7 Safe startup

Before a state-changing test, the suite shall establish or verify the declared safe starting state.

### 18.8 Safe teardown

HIL teardown shall attempt the declared safe state after:

- PASS;
- assertion failure;
- protocol error;
- timeout;
- operator stop;
- suite setup failure after partial connection;
- unexpected exception.

Teardown failure shall be visible and shall not be hidden by the original test result.

### 18.9 Physical oracles

A HIL test shall use an oracle suitable for the declared objective, such as:

- device acknowledgement;
- status query;
- readback query;
- independent DMM measurement;
- oscilloscope measurement;
- logic-analyser observation;
- relay-state feedback;
- environmental sensor;
- device diagnostic log;
- reference load;
- operator inspection where automation is not possible.

The oracle and tolerance shall be declared before execution.

### 18.10 Calibration and traceability

When a result depends on measurement accuracy, the required calibration status and validity of reference equipment shall be recorded.

RFDS-009 does not itself define laboratory accreditation requirements.

### 18.11 HIL skips

A missing device, fixture, reference instrument, operator action, or approved environment may produce SKIP only when the prerequisite and skip rule were declared before execution.

An unexpected connection failure during an available HIL run should normally be FAIL, not SKIP.

---

## 19. Multi-Driver and Bench Tests

Where a test uses multiple RFDS drivers, the bench shall be described by RFDS-018 or an approved equivalent.

The test plan shall define:

- physical topology;
- signal producers and consumers;
- relay and multiplexer paths;
- shared resources;
- resource ownership;
- connection ordering;
- safe startup sequence;
- stabilization rules;
- measurement source preference;
- pass/fail oracles;
- cleanup ordering;
- emergency shutdown;
- parallel-execution constraints.

Multi-driver tests shall not assume a connection or wiring path that is absent from the authoritative bench contract.

---

## 20. Safety Test Requirements

Safety tests shall verify applicable controls at the responsible layer.

They shall cover as applicable:

- minimum and maximum argument limits;
- cross-parameter limits;
- forbidden mode combinations;
- channel interlocks;
- output-disabled default state;
- safe initialization;
- safe reset;
- safe disconnect;
- safe teardown;
- behaviour after timeout;
- behaviour after transport disconnect;
- behaviour after malformed response;
- prevention of duplicate non-idempotent commands during retry;
- emergency shutdown keyword or procedure;
- bench-level forbidden sequences;
- required operator confirmation;
- resource locking.

A safety test that can create a hazardous state shall require an explicitly approved HIL profile and shall not run in ordinary CI.

---

## 21. Error, Timeout, and Recovery Tests

Tests shall verify every documented error category applicable to the driver.

At minimum, test as applicable:

- invalid argument;
- invalid state;
- unsupported operation;
- configuration error;
- dependency or vendor-runtime error;
- connection failure;
- transport timeout;
- write failure;
- read failure;
- malformed response;
- empty response;
- incomplete frame;
- checksum failure;
- device-reported error;
- resource busy;
- session not found;
- unsafe operation rejected;
- recovery failure;
- teardown failure.

For recoverable errors, tests shall verify:

1. the expected failure is reported;
2. the driver state after failure is documented and correct;
3. recovery or reconnect executes according to policy;
4. a known-good subsequent operation succeeds;
5. no unsafe residual state remains.

For non-recoverable errors, tests shall verify that the driver fails visibly and does not claim restored communication.

---

## 22. Regression-Test Requirements

### 22.1 Corrected defects

Every corrected defect that can be reproduced deterministically shall receive a regression test.

The regression test shall:

- fail on the known defective revision or reproduce the previous failure condition;
- pass on the corrected revision;
- identify the issue, requirement, review finding, or history entry;
- use the lowest effective test layer;
- include a Robot Framework regression test when the defect was user-visible and practical to reproduce through the public API.

### 22.2 Regression preservation

Regression tests shall remain active unless:

- the affected feature is formally removed;
- the test is replaced by stronger coverage;
- the test is no longer applicable due to an approved breaking change.

Removal shall be documented in history and review evidence.

### 22.3 Border-case defects

Defects involving limits shall receive tests immediately below, at, and immediately above the relevant boundary where meaningful.

### 22.4 Non-deterministic defects

When a defect cannot be reproduced deterministically, the project shall document:

- observed symptoms;
- available evidence;
- suspected mechanism;
- added diagnostics;
- risk;
- planned validation method;
- whether a soak, stress, or HIL test is required.

---

## 23. Compatibility Tests

Compatibility tests shall verify the declared support matrix.

They shall cover as applicable:

- minimum supported Python version;
- maximum tested Python version;
- minimum supported Robot Framework version;
- maximum tested Robot Framework version;
- primary operating systems;
- dependency lower and upper bounds where maintained;
- public keyword names;
- argument order and defaults;
- aliases;
- return schemas;
- exception categories;
- configuration-file compatibility;
- AI contract compatibility;
- supported device models;
- supported firmware revisions.

A support claim shall not be broader than the tested or explicitly provisional compatibility evidence.

Public API changes shall be compared with the previous approved release and classified as:

- compatible addition;
- compatible correction;
- deprecation;
- breaking change;
- internal-only change.

Undocumented breaking changes shall fail release testing.

---

## 24. Performance, Stress, Soak, and Concurrency Tests

These tests are mandatory when the device scope, transport, state model, or release task requires them.

### 24.1 Performance tests

Performance tests may verify:

- connection time;
- command latency;
- query latency;
- acquisition throughput;
- large-block transfer time;
- report or file export time;
- simulator overhead;
- retry completion time.

Thresholds shall be device- and environment-specific.

### 24.2 Stress tests

Stress tests may verify:

- repeated connect/disconnect;
- rapid command sequences within supported limits;
- large data transfers;
- maximum channel count;
- maximum scan list;
- repeated error injection;
- high report volume;
- resource exhaustion handling.

### 24.3 Soak tests

Soak tests shall define:

- duration;
- workload;
- polling or acquisition interval;
- acceptable error count;
- acceptable reconnect count;
- memory-growth limit;
- file or handle leak criteria;
- evidence-sampling interval;
- stop conditions.

### 24.4 Concurrency tests

When concurrent access is supported, tests shall verify:

- session isolation;
- lock ownership;
- command ordering;
- thread safety;
- no response cross-talk;
- no shared mutable-state corruption;
- deterministic resource-busy behaviour;
- safe close while another operation is active, if supported.

When concurrency is not supported, tests shall verify that unsafe parallel access is rejected or serialized according to policy.

### 24.5 Benchmark stability

Performance thresholds shall account for expected environment variation. Tests shall avoid brittle timing assertions that fail due only to ordinary CI scheduling noise.

---

## 25. Test Data and Fixture Control

### 25.1 Version control

Test vectors, simulator scenarios, schemas, and sanitized captures used for acceptance shall be version controlled.

### 25.2 Immutability during execution

Tests shall not modify authoritative golden data in place.

Generated output shall be written under the results directory or a temporary directory.

### 25.3 Data provenance

Reference data shall identify, where applicable:

- source document or capture;
- protocol revision;
- device model;
- firmware revision;
- fixture;
- date;
- author or generator;
- checksum;
- approval status.

### 25.4 Secrets and privacy

Test data and evidence shall not contain:

- credentials;
- private keys;
- tokens;
- personal filesystem paths;
- unnecessary personal names;
- uncontrolled private network information;
- customer or DUT confidential data without approved handling.

### 25.5 Temporary resources

Tests shall use isolated temporary directories, ports, and files where practical and shall clean them after execution.

---

## 26. Mocking and Test Doubles

### 26.1 Appropriate use

Mocks and fakes may be used to isolate:

- time;
- filesystem;
- environment variables;
- vendor SDKs;
- transport failures;
- operator input;
- deterministic retry sequence;
- external services.

### 26.2 Boundary selection

The test double shall be placed at the lowest boundary that still proves the intended behaviour.

### 26.3 Prohibited false confidence

A test shall not claim protocol conformance when it mocks the protocol builder or transport before serialized device data can be observed.

### 26.4 Behaviour verification

Tests should prefer verifying meaningful state, values, protocol data, and outcomes over asserting excessive internal call order.

---

## 27. Code-Coverage Requirements

### 27.1 Coverage scope

Coverage shall include all production Python code in the released driver package, excluding only reviewed categories such as:

- generated code;
- type-checking-only branches;
- operating-system branches that are separately exercised in the compatibility matrix;
- approved unreachable defensive guards;
- vendor code preserved unchanged and reviewed as an external dependency.

Exclusions shall be explicit and justified.

### 27.2 Default thresholds

Unless a stricter device-specific requirement is approved, each release shall meet at least:

| Scope | Line coverage | Branch coverage |
|---|---:|---:|
| Robot Framework adapter and converters | 95% | 90% |
| Combined non-GUI production code | 85% | 75% |
| Protocol builders and parsers | 95% | 90% |
| Safety, state, session, timeout, retry, and exception-mapping modules | 100% where practical | 100% where practical |

Any uncovered branch in a safety-critical or state-critical module shall be listed and justified in review evidence.

### 27.3 Coverage quality

Coverage percentage shall not replace meaningful assertions.

Tests written only to execute lines without verifying behaviour do not satisfy this standard.

### 27.4 Changed-code coverage

New or materially changed production code should meet at least 90% line coverage and 85% branch coverage unless a stricter module threshold applies.

### 27.5 Hardware-only code

Code executable only with hardware should be structured so that as much logic as practical remains unit- or simulator-testable.

Hardware-only exclusions shall be identified explicitly.

---

## 28. Test Result Statuses

Permitted statuses are:

- **PASS** — all required oracles passed;
- **FAIL** — one or more required oracles failed;
- **SKIP** — a declared prerequisite was unavailable or a declared condition made execution inapplicable for this run;
- **EXCLUDED** — the test is formally prohibited or not applicable, with an approved reason;
- **QUARANTINED** — the test is isolated due to an active test defect or unresolved instability, with owner, issue, and expiry review;
- **NOT RUN** — no execution occurred.

### 28.1 Release treatment

For mandatory release tests:

- FAIL is release-blocking;
- unexplained SKIP is release-blocking;
- unapproved EXCLUDED is release-blocking;
- QUARANTINED is release-blocking unless formally accepted by release authority with documented residual risk;
- NOT RUN is release-blocking.

### 28.2 Skip reason

A SKIP shall identify the unavailable prerequisite or selection rule.

Generic reasons such as `not available` are insufficient.

### 28.3 Exclusion record

An exclusion shall identify:

- test or requirement;
- reason;
- risk;
- approval;
- scope;
- review date;
- replacement evidence if any.

---

## 29. Flaky-Test Policy

### 29.1 Definition

A test is flaky when identical controlled inputs and environment can produce inconsistent outcomes.

### 29.2 Release policy

Known flaky tests shall not remain silently active in the mandatory release suite.

They shall be:

1. corrected;
2. replaced;
3. quarantined with an issue, owner, evidence, and review deadline; or
4. removed only with documented justification and replacement coverage.

### 29.3 Retries

Automatic test retries shall not convert a flaky FAIL into an unqualified PASS.

When retries are used for diagnosis or an approved unstable external environment, evidence shall preserve:

- each attempt;
- first failure;
- final result;
- retry reason;
- configured retry count.

### 29.4 Flakiness metrics

Long-running projects should track:

- flaky test count;
- retry-pass count;
- intermittent HIL failure rate;
- simulator nondeterminism;
- median time to correct quarantined tests.

---

## 30. Test Execution and Runner Requirements

### 30.1 Software test runners

`run_tests.*` shall:

- resolve the project root from the script location;
- verify the supported Python environment;
- run the approved software-only test set;
- execute unit, integration, replay, Robot simulator, compatibility subset, and applicable conformance-simulator tests;
- enforce coverage thresholds;
- write results under a timestamped directory;
- return a non-zero exit code on failure;
- display a concise result summary;
- never require real hardware by default.

### 30.2 HIL runners

`run_hil_tests.*` shall:

- require explicit HIL enablement;
- load a declared HIL profile;
- reject missing safety limits or required resources;
- acquire resource locks;
- verify expected device identity where possible;
- show the selected profile and prohibited operations;
- preserve Robot and additional evidence;
- release locks and attempt safe teardown;
- return a non-zero exit code on failure.

### 30.3 Working-directory independence

Runners shall work from any current working directory.

### 30.4 Output selection

Runners shall allow a caller-selected result directory while providing a safe default.

### 30.5 Help

Each runner shall provide help text with at least one software-only and one applicable HIL example.

---

## 31. CI Requirements

### 31.1 Software-only CI

Normal pull-request and branch CI shall run without physical hardware.

It shall execute as applicable:

- structure validation;
- package import test;
- formatting and lint checks;
- type checks;
- unit tests;
- integration tests;
- replay tests;
- simulator-backed Robot tests;
- compatibility matrix;
- RFDS-019 simulator conformance;
- coverage enforcement;
- Libdoc generation;
- AI contract validation;
- public API comparison;
- documentation build;
- clean-install smoke test.

### 31.2 HIL CI

HIL workflows shall be manually approved or restricted to controlled runners.

They shall use:

- resource inventory;
- resource locking;
- explicit safety profile;
- controlled credentials or resource configuration;
- timeout for the complete job;
- safe cleanup;
- evidence upload;
- no automatic execution on untrusted contributions when hardware safety could be affected.

### 31.3 Matrix coverage

The CI matrix shall cover the declared supported Python and Robot Framework versions at an appropriate cadence.

### 31.4 Release workflow

The release workflow shall reject release when mandatory test evidence is missing or stale for the candidate revision.

---

## 32. Evidence and Reporting

### 32.1 Mandatory environment evidence

Each release-relevant run shall record as applicable:

- project and driver version;
- commit or source revision;
- Python version;
- Robot Framework version;
- operating system;
- dependency versions;
- test profile;
- simulator or replay version;
- HIL device identity;
- firmware version;
- transport type and redacted resource;
- fixture and reference-equipment identity;
- safety limits;
- start and end time;
- pass, fail, skip, excluded, quarantined, and not-run totals.

### 32.2 Mandatory software evidence

Software test evidence shall include as applicable:

- pytest or equivalent machine-readable results;
- coverage XML and HTML or equivalent;
- Robot `output.xml`;
- Robot `log.html`;
- Robot `report.html`;
- compatibility results;
- replay or simulator result summary;
- conformance summary;
- environment record;
- skipped and excluded test report;
- Markdown summary.

### 32.3 Mandatory HIL evidence

HIL evidence shall include as applicable:

- Robot result files;
- hardware identity;
- effective HIL profile;
- safety limits;
- command and response traces;
- measurement logs;
- CSV or JSON data;
- plots when needed to interpret physical behaviour;
- fixture mapping;
- operator actions;
- cleanup result;
- calibration status of reference equipment when relevant;
- Markdown summary and verdict.

### 32.4 Recommended results layout

```text
results/<profile>/<timestamp>/
├── summary.md
├── environment.json
├── test_profile.yaml
├── pytest.xml
├── coverage.xml
├── coverage_html/
├── output.xml
├── log.html
├── report.html
├── compatibility.json
├── protocol_trace.log
├── measurements.csv
├── device_identity.json
├── fixture_identity.json
├── skips_exclusions.json
└── artifacts/
```

### 32.5 Evidence correlation

Evidence entries shall identify the test case, keyword, protocol vector, requirement, or measurement step that produced them.

### 32.6 Secret redaction

Evidence shall redact credentials and other secrets.

---

## 33. Traceability Requirements

The project shall maintain traceability between:

```text
RFDS or device requirement
        ↓
Public capability / Robot keyword
        ↓
AI contract capability
        ↓
Implementation symbol
        ↓
Unit or component test
        ↓
Robot acceptance or conformance test
        ↓
HIL or physical validation where applicable
        ↓
Evidence and review verdict
        ↓
History entry and released package
```

The traceability matrix shall identify at least:

- requirement identifier;
- implementation location;
- unit test;
- integration or replay test;
- Robot test;
- RFDS-019 vector where applicable;
- HIL test where applicable;
- evidence reference;
- status;
- justification for deferred or not-applicable items.

A requirement shall not be marked fully hardware-validated without HIL evidence when physical behaviour is part of that requirement.

---

## 34. Test Review Requirements

Each gate or release review shall evaluate:

- test scope completeness;
- appropriate layer selection;
- assertion quality;
- boundary and negative coverage;
- simulator fidelity;
- simulator limitations;
- Robot public-API coverage;
- RFDS-019 coverage;
- HIL scope and safety;
- coverage thresholds;
- skipped and excluded tests;
- flaky or quarantined tests;
- regression-test completeness;
- evidence reproducibility;
- traceability;
- residual hardware-validation gaps.

Review findings shall use the project severity model and shall identify corrective action and residual risk.

---

## 35. Lifecycle and Gate Integration

### 35.1 Gate 1 — Architecture and Skeleton

Required test outputs include:

- test directory skeleton;
- test strategy for the phase;
- simulator or replay architecture;
- unit-test harness;
- initial package import test;
- declared HIL prerequisites and safety profile template.

### 35.2 Gate 2 — Core Implementation

Required test outputs include:

- unit tests for implemented core behaviour;
- protocol serialization and parsing tests;
- transport tests;
- initial Robot acceptance tests;
- regression tests for corrected defects.

### 35.3 Gate 3 — Extended Features

Required test outputs include:

- tests for added capabilities and edge cases;
- expanded simulator scenarios;
- compatibility tests;
- recovery and safety tests;
- performance tests where feature scope requires them;
- AI contract verification-objective updates.

### 35.4 Gate 4 — Tests and Documentation

Required test outputs include:

- complete phase unit and integration tests;
- complete simulator and replay validation;
- complete phase Robot acceptance coverage;
- applicable RFDS-019 conformance coverage;
- coverage report;
- HIL execution where available and safe;
- test execution documentation;
- updated examples and run scripts.

### 35.5 Gate 5 — Review and Release

Required test outputs include:

- clean release regression run;
- compatibility verdict;
- simulator-validation verdict;
- HIL status and evidence;
- conformance verdict;
- performance or soak verdict where applicable;
- skipped, excluded, quarantined, and not-run review;
- traceability update;
- release-readiness test summary.

A phase shall not be approved when mandatory tests for that phase remain NOT RUN without an approved deferral.

---

## 36. Release Qualification Levels

A driver revision shall declare one of the following qualification levels or an approved equivalent:

### Q0 — Buildable

- package imports;
- test harness exists;
- no hardware claim.

### Q1 — Unit Validated

- applicable unit tests pass;
- coverage threshold for implemented scope passes;
- no simulator or hardware claim.

### Q2 — Software Integrated

- unit, integration, replay, and simulator tests pass;
- Robot software acceptance tests pass;
- no hardware claim.

### Q3 — Protocol Conformant

- Q2 passed;
- applicable RFDS-019 conformance requirements pass using approved simulator and/or protocol observation;
- physical-function accuracy is not implied.

### Q4 — Representative Hardware Validated

- Q3 passed;
- representative supported hardware tests pass;
- tested models, firmware, transports, fixtures, and limits are identified.

### Q5 — HIL Qualified

- full approved HIL matrix for the declared release scope passes;
- physical-function, safety, recovery, and applicable performance evidence exists;
- remaining exclusions are approved.

The README, release notes, GitHub Pages, and AI contract limitations shall state the actual qualification level.

---

## 37. Acceptance Criteria

A released driver passes RFDS-009 only when all applicable conditions are satisfied:

1. the mandatory test directories and runners exist;
2. software-only tests execute without uncontrolled hardware;
3. unit tests cover core logic, parsing, validation, state, errors, and safety functions;
4. protocol serialization and parsing have independent deterministic oracles;
5. transport adapters are tested for success, failure, timeout, and cleanup;
6. replay or approved simulator validation exists;
7. simulator limitations are documented;
8. Robot Framework acceptance tests exercise the public API;
9. RFDS-019 conformance passes or approved exclusions are documented;
10. HIL status is explicit and truthful;
11. applicable real-device tests pass for the claimed qualification level;
12. safety setup, limits, teardown, and fault cleanup are verified;
13. documented recoverable errors have recovery tests;
14. corrected deterministic defects have regression tests;
15. compatibility tests support the declared compatibility matrix;
16. applicable performance, stress, soak, and concurrency tests pass;
17. default coverage thresholds or approved stricter thresholds pass;
18. no mandatory test is unexplained SKIP, unapproved EXCLUDED, QUARANTINED without release acceptance, or NOT RUN;
19. known flaky tests are corrected or formally controlled;
20. evidence records environment, versions, profiles, and hardware identity where applicable;
21. results are traceable to requirements and release review;
22. the release documentation states the actual validation and HIL status;
23. all test evidence corresponds to the exact candidate revision;
24. no Critical testing or safety finding remains open;
25. Major findings are corrected or formally accepted by release authority.

---

## 38. Failure Conditions

RFDS-009 shall fail when any applicable condition occurs:

- tests require undocumented execution order;
- software-only CI unexpectedly accesses hardware;
- a mandatory test can block indefinitely;
- a test passes only because no exception was raised;
- protocol expectations are generated by the same unverified code under test without an independent oracle;
- simulator state leaks between tests unintentionally;
- a simulator pass is described as proof of physical accuracy or safety;
- HIL silently falls back to simulation;
- HIL runs without required safety limits or resource profile;
- teardown failure is hidden;
- an unexpected hardware connection failure is incorrectly reported as a harmless skip;
- a corrected deterministic defect has no regression test without justification;
- coverage is below threshold;
- safety-critical uncovered branches lack approved justification;
- mandatory public Robot behaviour is untested;
- RFDS-019 conformance is omitted without approval;
- required hardware qualification is claimed without evidence;
- test evidence belongs to a different revision;
- required environment or device identity evidence is missing;
- retries conceal flaky tests;
- mandatory tests are NOT RUN;
- exclusions are unapproved or generic;
- test data contains secrets;
- release documentation overstates test status;
- unresolved Critical findings remain.

---

## 39. Minimum Definition of Done

RFDS-009 is complete for a released driver when:

- the project has a layered test strategy;
- unit, protocol, transport, replay or simulator, integration, and Robot tests exist for the supported scope;
- RFDS-019 conformance is integrated;
- real-device status is explicit;
- HIL tests are safe, controlled, and evidenced when applicable;
- corrected defects have regression coverage;
- coverage thresholds pass;
- compatibility and applicable performance requirements pass;
- all mandatory results are traceable;
- no mandatory test remains NOT RUN;
- the release review records the final qualification level and residual risks.

---

## 40. Review Checklist

1. Are all applicable test layers present?
2. Can the complete software-only suite run without hardware?
3. Are unit tests deterministic and meaningful?
4. Are command builders and response parsers tested independently?
5. Are transport timeout, disconnect, and cleanup paths tested?
6. Is replay or an approved simulator available?
7. Does the simulator operate at the real device-facing boundary?
8. Are simulator limitations explicit?
9. Are public Robot Framework behaviours tested through Robot Framework?
10. Is RFDS-019 conformance present and current?
11. Are all supported public keywords represented in conformance inventory?
12. Is HIL disabled by default?
13. Does HIL require explicit safety and resource configuration?
14. Is silent HIL-to-simulator fallback prevented?
15. Are real device, firmware, transport, fixture, and reference-equipment identities recorded?
16. Are safe startup and teardown verified?
17. Are negative, boundary, timeout, and malformed-response cases covered?
18. Is recovery verified after recoverable faults?
19. Does every corrected deterministic defect have a regression test?
20. Do coverage thresholds pass?
21. Are safety-critical uncovered branches justified?
22. Are skipped, excluded, quarantined, and not-run tests reviewed?
23. Are retries preserving first-failure evidence?
24. Are flaky tests controlled rather than hidden?
25. Does the compatibility matrix match test evidence?
26. Are performance, stress, soak, and concurrency tests present where required?
27. Is every test run bounded by finite timeouts?
28. Are test data and evidence sanitized?
29. Are results traceable to requirements and the exact release revision?
30. Does release documentation state the true qualification level?

---

## Appendix A — Minimum Test Matrix by Driver Capability

| Capability | Unit | Simulator/replay | Robot | RFDS-019 | HIL |
|---|---|---|---|---|---|
| Connection lifecycle | Required | Required | Required | Required | Representative required |
| Identity query | Parser required | Required | Required | Required | Required when hardware-supported |
| Configuration/write operation | Validation and serialization required | Required | Required | Required | Representative required |
| Query/read operation | Parsing required | Required | Required | Required | Representative required |
| Measurement | Conversion and parsing required | Required | Required | Required | Physical oracle required for accuracy claim |
| Output/actuation | Limits and state required | Required | Required | Required | Safe-output HIL required for hardware claim |
| Error queue/status | Parsing and mapping required | Required | Required | Required | Representative required |
| Timeout/retry | Required | Fault injection required | Required | Required where applicable | Representative where practical |
| Recovery/reconnect | Required | Required | Required | Required where applicable | Required for hardware recovery claim |
| Multi-session | Ownership required | Required | Required | As applicable | Required if hardware concurrency is claimed |
| Diagnostics export | Required | Required | Required | Non-device-facing inventory as applicable | Representative |
| Safe teardown | Required | Required | Required | As applicable | Required |

---

## Appendix B — Recommended Robot Tags

Recommended tags include:

```text
unit
integration
robot
simulator
replay
conformance
hil
hil-read-only
hil-safe-output
hil-full
performance
stress
soak
compatibility
regression
safety
recovery
manual
operator-action
exclusive-resource
```

Tags shall describe execution requirements and evidence scope. A `hil` tag shall never be used for a simulator-only test.

---

## Appendix C — Example HIL Resource Profile

```yaml
profile_id: hil_safe_output
hil_enabled: false
qualification_scope: representative_hardware

driver:
  name: rf_example_driver
  version: "26.01"

primary_device:
  resource: "${DEVICE_RESOURCE}"
  expected_manufacturer: "ExampleCorp"
  expected_model: "EX1000"
  allowed_firmware:
    - ">=1.2.0,<2.0.0"

transport:
  type: tcp
  timeout_s: 5

safety:
  maximum_voltage_v: 5.0
  maximum_current_a: 0.1
  output_must_start_disabled: true
  output_must_end_disabled: true
  emergency_shutdown_keyword: Emergency Shutdown

operations:
  allowed:
    - identity
    - status
    - set_voltage
    - measure_voltage
  prohibited:
    - calibration_write
    - firmware_update
    - factory_reset

fixture:
  id: "${FIXTURE_ID}"
  operator_action_required: false

reference_instrument:
  resource: "${DMM_RESOURCE}"
  maximum_age_of_calibration_days: 365

resources:
  lock_ids:
    - "${DEVICE_LOCK_ID}"
    - "${DMM_LOCK_ID}"

results:
  output_root: results/hil_safe_output
```

This example is illustrative. Device-specific profiles shall define the actual safe limits and topology.

---

## Appendix D — Example Test Evidence Summary

```markdown
# RFDS-009 Test Summary

- Driver: rf_example_driver
- Driver version: 26.01
- Source revision: <commit>
- Profile: conformance_simulator
- Python: 3.x
- Robot Framework: 7.x
- Simulator: example-simulator 1.2
- HIL used: No
- Qualification supported by this run: Q3 Protocol Conformant

## Results

| Layer | Passed | Failed | Skipped | Excluded | Not run |
|---|---:|---:|---:|---:|---:|
| Unit | 140 | 0 | 0 | 0 | 0 |
| Integration | 35 | 0 | 0 | 0 | 0 |
| Replay | 24 | 0 | 0 | 0 | 0 |
| Robot | 42 | 0 | 0 | 0 | 0 |
| RFDS-019 | 58 | 0 | 0 | 2 | 0 |

## Coverage

- Combined line coverage: 91%
- Combined branch coverage: 84%
- Safety/state/session modules: 100%

## Limitations

- No physical output accuracy is proven by this run.
- Hardware validation remains required for Q4 or Q5 qualification.
```

---

## Appendix E — Relationship Between RFDS-009 and RFDS-019

| Subject | RFDS-009 | RFDS-019 |
|---|---|---|
| Overall test strategy | Authoritative | Out of scope |
| Unit-test coverage | Authoritative | Out of scope |
| Simulator and replay requirements | General authoritative requirements | Uses simulator for protocol conformance |
| Robot Framework acceptance tests | Authoritative | Specialized exhaustive callability test |
| Public keyword inventory | References RFDS-019 | Authoritative |
| Outbound protocol verification | General testing context | Authoritative for public keyword conformance |
| Inbound response and parsed return | General testing context | Authoritative for public keyword conformance |
| HIL safety and resource profiles | Authoritative | Uses real device where safe and practical |
| Physical accuracy | Authoritative test framework when required | Out of scope |
| Performance and soak | Authoritative | Out of scope |
| Release qualification | Authoritative | One required evidence layer |

RFDS-009 and RFDS-019 are complementary. Passing either document alone shall not be represented as passing the complete RFDS production release process.

---

## Appendix F — Changes in Version 1.0

Version 1.0 establishes:

- the complete RFDS driver test-layer model;
- mandatory unit, integration, replay, simulator, Robot, conformance, HIL, compatibility, regression, and applicable performance testing;
- explicit separation between simulator evidence and physical hardware evidence;
- safe and explicitly enabled HIL execution;
- default coverage thresholds;
- regression-test requirements for corrected defects;
- flaky-test and retry policy;
- test evidence, status, traceability, qualification levels, acceptance criteria, and release failure conditions;
- formal integration with RFDS-017, RFDS-018, RFDS-019, RFDS-005, RFDS-001, and the RFDS implementation lifecycle.
