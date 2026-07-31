# RFDS-012 — GUI Integration Specification

**Document ID:** RFDS-012  
**Version:** 1.0  
**Status:** Draft Project Standard (Normative)  
**Applies to:** Generic operator GUIs, GUI integration adapters, bench-control applications, and RFDS driver packages claiming generic GUI compatibility

---

## 1. Purpose

This specification defines the mandatory integration rules that allow a generic operator GUI to discover, display, configure, and safely operate RFDS Robot Framework drivers without embedding vendor-specific protocol logic.

The GUI shall provide a consistent operator experience while preserving the RFDS execution, metadata, safety, configuration, evidence, and conformance boundaries.

The required logical path is:

```text
Operator intent
      ↓
Generic GUI presentation
      ↓
GUI controller and policy layer
      ↓
Approved public driver capability / Robot Framework keyword
      ↓
Driver service, protocol, and transport layers
      ↓
Physical device or approved simulator
      ↓
Typed result, state update, or documented failure
      ↓
GUI display, evidence, and operator guidance
```

A GUI conforming to RFDS-012 shall be able to integrate a new RFDS driver primarily from machine-readable metadata and the stable public API, rather than from hard-coded knowledge of a specific manufacturer or model.

---

## 2. Scope

### 2.1 In scope

RFDS-012 covers:

- driver discovery and compatibility assessment;
- loading and validating RFDS-017 driver contracts;
- loading RFDS-018 bench contracts when a deployed bench is controlled;
- mapping public driver capabilities to generic GUI controls;
- connection, identity, session, state, and resource presentation;
- capability enablement based on preconditions and current state;
- argument entry, validation, unit display, and return-value presentation;
- asynchronous execution of driver operations;
- long-running operation progress, stop, abort, timeout, and recovery behaviour;
- manual operator control;
- Robot Framework suite and workflow execution;
- multi-driver bench coordination;
- operator actions, confirmations, interlocks, and emergency workflows;
- configuration import, validation, preview, application, and export;
- logging, evidence, diagnostics, and result export;
- role-based authorization where required;
- generic and optional device-specific GUI extensions;
- simulator and real-hardware modes;
- GUI integration tests, review, and release acceptance.

### 2.2 Out of scope

RFDS-012 does not define:

- vendor protocol syntax;
- transport implementation;
- the semantic behaviour of public driver keywords;
- the complete RFDS-017 or RFDS-018 schema;
- physical bench wiring that is not declared in RFDS-018;
- device calibration or measurement-accuracy requirements;
- complete functional-safety certification;
- a mandatory visual brand, colour palette, or widget toolkit;
- a specific desktop, web, or mobile framework;
- automatic generation of test requirements;
- replacement of Robot Framework reporting;
- replacement of driver-level, fixture-level, or bench-level safety controls.

A conforming GUI may add device-specific panels, but those panels shall remain subject to the same public-API, safety, evidence, and lifecycle requirements.

---

## 3. Normative References

RFDS-012 shall be applied together with the latest approved revisions of:

- **RFDS-001 — Platform Requirements**;
- **RFDS-002 — Mandatory Public API and Robot Framework Keyword Standard**;
- **RFDS-005 — Driver Package Specification**;
- **RFDS-006 — Coding Standard**;
- **RFDS-007 — Error and Exception Standard**;
- **RFDS-008 — Logging and Evidence Standard**;
- **RFDS-009 — Testing Standard**;
- **RFDS-010 — Driver Review Checklist**;
- **RFDS-011 — Release Process**;
- **RFDS-013 — Capability Model**, when approved;
- **RFDS-014 — Driver Configuration Model Specification**, when approved;
- **RFDS-015 — Plugin Architecture**, when approved;
- **RFDS-017 — AI Driver Contract Specification v3.0 or later**;
- **RFDS-018 — AI Test Bench Contract Specification**;
- **RFDS-019 — Driver Call and Protocol Conformance Test Specification**;
- **RFDS-020 — Driver Implementation Lifecycle v1.1 or later**;
- the device-specific implementation task;
- applicable vendor documentation and approved bench procedures.

### 3.1 Requirement precedence

When requirements conflict, precedence shall be:

1. approved safety and emergency requirements;
2. RFDS-018 deployed bench constraints and physical topology;
3. approved device-specific limitations;
4. RFDS-017 driver capability semantics;
5. the current public driver API and verified runtime state;
6. RFDS-012 GUI presentation rules;
7. optional GUI presentation hints.

A conflict shall not be silently resolved by the GUI. The affected operation shall be disabled or blocked, and the conflict shall be reported with actionable diagnostics.

---

## 4. Normative Terminology

- **shall / shall not** — mandatory requirement;
- **should / should not** — recommended requirement; deviation requires reviewed justification;
- **may** — permitted implementation choice.

Additional terms:

- **Generic GUI** — an operator application that integrates drivers from declared capabilities and contracts rather than model-specific protocol code.
- **GUI adapter** — the component that maps GUI requests to approved public driver calls and maps results or errors back to the GUI.
- **Capability** — a declared public operation, normally corresponding to one Robot Framework keyword.
- **Presentation hint** — optional metadata affecting grouping, order, labels, help text, or control appearance without changing semantics.
- **Active operation** — an operation that changes device, fixture, DUT, calibration, file, firmware, or bench state.
- **Read-only operation** — an operation declared to have no device or bench side effect.
- **Dangerous or destructive operation** — an operation whose RFDS-017 or bench classification requires special authorization, confirmation, fixture, backup, or recovery.
- **Fail closed** — refuse or disable an operation when required safety or semantic information is absent, stale, contradictory, or invalid.
- **Effective configuration** — the validated configuration after applying documented precedence, with secrets redacted for display and evidence.

---

## 5. Design Principles

A conforming implementation shall follow these principles.

### 5.1 Metadata-driven integration

The GUI shall build its generic device model from RFDS contracts, runtime capability information, configuration schemas, and the public API. It shall not select behaviour by testing for a vendor, model name, Python class name, or private implementation symbol when a declared capability can be used.

### 5.2 Public API only

The GUI shall invoke only approved public driver capabilities. It shall not:

- call private Python methods;
- construct protocol commands or frames;
- access transport objects directly;
- modify internal driver state;
- bypass argument validation, state checks, retries, timeouts, or safety policy;
- duplicate vendor protocol logic in the GUI.

### 5.3 Separation of semantics and presentation

RFDS-017 and the public driver API define operation semantics. RFDS-018 defines deployed bench topology and bench-wide constraints. GUI metadata may control presentation only.

### 5.4 Fail-closed control

Missing cosmetic information may use a safe generic presentation. Missing or contradictory safety-critical information shall disable the affected operation.

### 5.5 Explicit hardware mode

Simulation, replay, disconnected, and real-hardware modes shall be visually distinct. A real connection failure shall not silently fall back to simulation.

### 5.6 Evidence by default

Every operator invocation shall create traceable evidence sufficient to determine what was requested, which driver and device were targeted, what result occurred, and whether cleanup succeeded.

### 5.7 No false assurance

The GUI shall distinguish:

- command requested;
- command accepted;
- driver call completed;
- device read-back confirmed;
- physical state independently verified.

A successful return from a command shall not be presented as independent physical verification unless the declared oracle supports that conclusion.

### 5.8 Safety is layered

GUI disablement, confirmation dialogs, and role checks are usability and policy controls. They shall not be represented as substitutes for driver, fixture, hardware, or bench interlocks.

---

## 6. Reference Architecture

A generic GUI should use the following responsibility boundaries:

```text
┌──────────────────────────────────────────────────────────────┐
│ Presentation layer                                           │
│ Views, controls, tables, plots, accessibility, localization  │
└──────────────────────────────┬───────────────────────────────┘
                               │ typed UI intents/events
┌──────────────────────────────▼───────────────────────────────┐
│ GUI application/controller layer                             │
│ State projection, validation, authorization, workflow logic  │
└──────────────────────────────┬───────────────────────────────┘
                               │ approved operation request
┌──────────────────────────────▼───────────────────────────────┐
│ Invocation gateway / GUI adapter                             │
│ Public keyword mapping, timeout, correlation, result mapping │
└──────────────────────────────┬───────────────────────────────┘
                               │ public API only
┌──────────────────────────────▼───────────────────────────────┐
│ RFDS driver / Robot Framework execution layer                │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│ Device, simulator, or bench                                  │
└──────────────────────────────────────────────────────────────┘

Metadata and policy inputs:
RFDS-017 + RFDS-018 + runtime capability manifest + config schema
+ RFDS-019 status/evidence + authorization policy
```

### 6.1 Presentation layer

The presentation layer shall not own device semantics, protocol logic, safety limits, or resource locking.

### 6.2 Controller layer

The controller layer shall own:

- projected GUI state;
- control enablement;
- local form validation;
- operation queueing;
- authorization and confirmation workflow;
- result and evidence presentation;
- coordination with the invocation gateway.

### 6.3 Invocation gateway

The invocation gateway shall own:

- exact mapping to the public capability or Robot keyword;
- argument serialization using declared types;
- operation correlation identifiers;
- finite execution timeouts;
- driver/session selection;
- cancellation or stop routing where supported;
- structured result and error mapping;
- evidence hooks.

### 6.4 Driver ownership

The driver remains authoritative for:

- device semantics;
- transport and protocol handling;
- device-level validation;
- device state transitions;
- retry and recovery policy;
- safe-state actions declared by the driver;
- typed results and documented exceptions.

---

## 7. Authoritative Information and Conflict Handling

The GUI shall resolve information using the following model.

| Information | Authoritative source |
|---|---|
| Public capability name and signature | Released public API and RFDS-017 lock-validated contract |
| Preconditions, postconditions, side effects, risk, timing, retry, errors | RFDS-017 |
| Physical topology, shared resources, signal routing, bench limits | RFDS-018 |
| Live connection, device identity, operation result, current state | Driver runtime result |
| Protocol-call qualification | RFDS-019 evidence |
| Configuration fields and validation | Approved configuration schema |
| Control grouping, ordering, icons, short help | Optional presentation hints |

### 7.1 Stale contract handling

Before enabling active controls, the GUI shall compare, where available:

- driver package version;
- RFDS-017 generated-for version;
- public API manifest or lock;
- capability-manifest version;
- RFDS-018 referenced driver version.

If the contract and installed driver are inconsistent:

- active operations shall be disabled;
- read-only identification and diagnostic operations may remain available only when their signatures can be verified;
- the mismatch shall be shown prominently;
- the GUI shall not attempt to repair the mismatch by guessing renamed arguments or keywords.

### 7.2 `UNKNOWN` handling

An `UNKNOWN` value shall remain visible. The GUI shall not replace it with an assumed value.

If `UNKNOWN` affects safety, limits, required resources, preconditions, cleanup, or authorization, the affected operation shall be blocked until the value is resolved by an approved configuration or contract update.

### 7.3 Runtime contradiction

When runtime state contradicts cached state or contract expectations, the GUI shall:

1. mark the affected projection stale;
2. stop enabling dependent operations;
3. request a documented state refresh or resynchronization;
4. preserve the original contradiction in evidence;
5. require recovery or operator action when the state remains uncertain.

---

## 8. GUI Compatibility Levels

A driver or GUI integration may claim one or more levels only after meeting all requirements of that level and lower levels.

### 8.1 GUI-L0 — Metadata compatible

- the package imports without hardware activity;
- RFDS-017 loads and validates;
- public capabilities and signatures can be inventoried;
- driver identity and version can be displayed;
- unsupported or unknown metadata is reported deterministically.

### 8.2 GUI-L1 — Lifecycle and diagnostics compatible

- connection profiles can be presented;
- connect, verify communication, identify, diagnose, and disconnect operations are supported through the public API;
- state and errors are mapped to generic GUI status;
- all blocking operations have finite timeouts.

### 8.3 GUI-L2 — Generic manual-control compatible

- eligible public capabilities generate usable controls;
- inputs, defaults, enums, ranges, units, and return types are represented;
- preconditions and current state control enablement;
- active operations use confirmations and cleanup rules where required;
- operation evidence is generated.

### 8.4 GUI-L3 — Robot execution compatible

- Robot Framework suites and packaged examples can be selected and executed;
- variables and profiles are validated before execution;
- standard Robot reports are preserved;
- progress and stop behaviour are represented without false precision.

### 8.5 GUI-L4 — Bench-integrated compatible

- an RFDS-018 bench contract is loaded and validated;
- physical topology, operator actions, resource conflicts, safety zones, and emergency workflow are represented;
- multi-driver scheduling and exclusive-resource enforcement are implemented;
- the bench ends in a verified declared safe state.

### 8.6 GUI-L5 — Production compatible

- RFDS-019 evidence is current for enabled production capabilities;
- representative simulator and HIL GUI-integration tests pass;
- configuration, evidence, security, accessibility, documentation, and lifecycle requirements pass;
- no open Critical finding exists;
- all Major findings are corrected or formally accepted with visible residual risk.

A GUI shall display the claimed compatibility level and the evidence basis. It shall not represent a simulator-only result as real-device qualification.

---

## 9. Driver Eligibility for Generic GUI Loading

Before loading a driver as production-operable, the GUI shall verify that the driver provides or supports:

- stable package and library identity;
- a valid RFDS-017 contract;
- a current contract lock or equivalent API-drift check;
- deterministic public keyword inventory;
- no hardware activity during import or metadata discovery;
- explicit supported connection profiles;
- finite timeout behaviour;
- documented connection, identification, and disconnection behaviour;
- documented errors and recovery;
- safe-state and cleanup information when active operations exist;
- structured Robot Framework-compatible return values;
- RFDS-019 status or an explicit unverified classification;
- declared concurrency and resource-ownership rules.

A driver failing these checks may be listed as **INCOMPATIBLE**, **METADATA-ONLY**, or **DEVELOPMENT**, but shall not be silently treated as production-operable.

---

## 10. Capability Projection Requirements

The GUI shall create one inventory entry for every public capability, including aliases and deprecated keywords while they remain supported.

Each projected capability shall preserve at least:

- capability identifier;
- public Robot Framework keyword name;
- canonical keyword name;
- aliases and deprecation status;
- purpose and short operator description;
- argument names, order, required status, defaults, types, units, enums, and limits;
- return type and schema;
- preconditions and permitted source states;
- postconditions and expected destination states;
- side effects and persistence;
- risk classification;
- blocking and timing behaviour;
- stabilization delay;
- timeout and retry policy;
- required and exclusive resources;
- operator actions;
- cleanup or rollback action;
- errors and recovery guidance;
- simulator and hardware applicability;
- RFDS-019 qualification status;
- presentation classification.

### 10.1 Presentation classification

Every capability shall be assigned one GUI presentation status:

- **PRIMARY** — normal operator operation;
- **ADVANCED** — available in an advanced or engineering view;
- **WORKFLOW_ONLY** — callable only through an approved guided workflow;
- **READ_ONLY** — displayed as query or diagnostic action;
- **HIDDEN_INTERNAL** — permitted only when the item is not a public capability;
- **UNAVAILABLE** — public capability not executable in the current state, profile, role, or bench, with a visible reason;
- **DEPRECATED** — supported compatibility capability with replacement guidance.

A public capability shall not be omitted from the GUI inventory. Presentation status may restrict normal access, but the inventory and reason shall remain reviewable.

### 10.2 Presentation hints

Optional hints may define:

- category and subgroup;
- display order;
- concise label;
- icon identifier;
- preferred generic widget;
- help link;
- compact or advanced placement;
- recommended refresh policy;
- chart/table presentation preference.

Hints shall not redefine:

- keyword name or signature;
- type, unit, limit, enum, or default;
- risk level;
- state transition;
- side effect;
- timeout or retry policy;
- required resource;
- safety rule;
- cleanup requirement.

---

## 11. Generic Control Generation

### 11.1 Type-to-control mapping

The GUI shall support at least the following generic mappings:

| Declared input | Minimum generic control |
|---|---|
| Boolean | Checkbox, switch, or explicit true/false selector |
| Integer | Validated numeric field; spinner only when step is meaningful |
| Floating point | Validated numeric field with unit and declared precision |
| String | Text field with length, pattern, and secret handling where declared |
| Enum | Closed selector listing only declared values |
| Duration | Duration field accepting declared Robot time or normalized units |
| Channel/resource identifier | Selector populated from declared or discovered valid values |
| Path/file | Constrained file selector with mode, extension, and access validation |
| List | Repeatable validated entries or multi-select when values are closed |
| Dictionary/object | Schema-driven form or validated structured editor |
| Optional value | Explicit use-default/use-null control when omission has distinct semantics |

### 11.2 Validation

The GUI shall validate locally before invocation where the contract provides enough information. Local validation shall not replace driver validation.

Validation messages shall identify:

- field;
- rejected value, unless secret;
- applicable limit or accepted format;
- unit;
- whether the request was blocked before transmission.

### 11.3 Defaults

The GUI shall distinguish:

- argument omitted;
- argument supplied with the documented default;
- explicit null or none;
- inherited configuration value;
- live device value.

It shall not substitute a display default for an omitted argument when omission has different driver semantics.

### 11.4 Units

Units shall be displayed adjacent to values. Conversion may be offered only when:

- the base unit remains explicit;
- conversion is deterministic;
- the exact value sent to the driver is recorded;
- limits are applied in the authoritative unit;
- the GUI does not silently change engineering meaning.

### 11.5 Unknown or unsupported types

An unknown input type shall not produce an unrestricted generic text field for an active operation. The operation shall be unavailable until a safe control or approved structured editor exists.

---

## 12. Required Information Surfaces

A production generic GUI shall provide equivalent access to the following information, regardless of tab or page names.

### 12.1 System dashboard

The dashboard shall show:

- GUI version;
- selected bench or standalone mode;
- simulation versus real-hardware status;
- connected drivers and aliases;
- device identities and firmware when available;
- active, queued, failed, and recovering operations;
- safety and interlock status;
- current profile and authorization context;
- output/evidence location;
- unresolved warnings and contract mismatches.

### 12.2 Connections

The connection surface shall show connection profiles, resource identifiers, connection state, communication verification, identity, latency or timeout diagnostics when available, and disconnect controls.

### 12.3 Device operations

The device surface shall present projected public capabilities, current state, read-back values, applicable limits, and operation history.

### 12.4 Test execution

The test surface shall support approved Robot suites, examples, templates, variables, tags, profiles, output directory, execution status, and report links.

### 12.5 Results and evidence

The results surface shall provide run summaries, Robot reports, measurements, attachments, exported configuration, version evidence, and cleanup status.

### 12.6 Logs and diagnostics

The diagnostics surface shall provide structured event logs, filterable errors, driver diagnostics, session state, and diagnostic-bundle export with secrets redacted.

### 12.7 Configuration

The configuration surface shall provide profile selection, validation, diff preview, import, export, effective-configuration view, and source precedence.

### 12.8 Safety

The safety surface shall provide applicable limits, forbidden sequences, operator actions, safe startup and shutdown state, emergency workflow, interlock status, and verification status.

### 12.9 Help and identity

The GUI shall expose current driver documentation, contract version, package version, supported models, qualification status, known limitations, and deprecation guidance.

---

## 13. Driver Discovery and Loading

### 13.1 Discovery

Driver discovery shall be deterministic and shall not connect to hardware. It shall return enough metadata to display:

- package name and version;
- library import name;
- supported instrument class and models;
- supported transports;
- contract status;
- GUI compatibility level;
- simulator availability;
- qualification status.

### 13.2 Plugin loading

When RFDS-015 is available, the GUI shall use its approved plugin-discovery and loading mechanism.

Until then, the GUI shall use an allow-listed entry-point or configuration mechanism. It shall not scan and execute arbitrary Python files from user-selected directories.

### 13.3 Isolation

A load or metadata failure in one driver shall not corrupt the state of other loaded drivers. The failed driver shall be isolated and reported with its causal error.

### 13.4 Import safety

Importing a driver, reading its metadata, generating Libdoc, or building a GUI manifest shall not:

- open hardware sessions;
- change device state;
- start uncontrolled background threads;
- create persistent files outside declared cache/output locations;
- require a private bench resource.

---

## 14. Connection and Device Selection

### 14.1 Explicit connection

The GUI shall not auto-connect to real hardware unless an approved deployed profile explicitly requires it and the action is visible to the operator.

### 14.2 Resource selection

Resource selectors shall support applicable VISA, serial, LAN, USB, CAN, SDK, or simulator profiles without exposing private transport internals to normal operation panels.

Discovery results shall be treated as candidates, not verified device identity.

### 14.3 Identity verification

After connection, the GUI shall execute the declared communication or identity check. It shall compare the returned identity with supported models and configured expectations.

Unsupported or unexpected identity shall produce a blocking warning for active operations unless an approved compatibility rule exists.

### 14.4 Connection states

The GUI shall distinguish at least:

- `DISCONNECTED`;
- `CONNECTING`;
- `CONNECTED_UNVERIFIED`;
- `CONNECTED_VERIFIED`;
- `DEGRADED`;
- `RECOVERING`;
- `DISCONNECTING`;
- `ERROR`;
- `UNKNOWN`.

This is a GUI presentation-level projection, not an alternative state authority: it refines RFDS-003's canonical session-state enum (splitting `CONNECTED` into unverified/verified, and adding `UNKNOWN` for not-yet-queried GUI state). The GUI shall derive it deterministically from RFDS-003 states plus the GUI's own verification/query status, not define connection semantics independently.

A connection indicator shall not show verified operation solely because a transport object exists.

### 14.5 Repeated actions

Repeated connect and disconnect behaviour shall follow the driver contract. The GUI shall not create duplicate sessions when the selected alias or resource policy forbids them.

---

## 15. Session, Alias, State, and Resource Model

### 15.1 Session identity

Every GUI operation shall target an explicit driver instance and session alias. The GUI shall avoid ambiguous global concepts such as “current instrument” when more than one session exists.

### 15.2 State projection

The GUI shall project driver state from declared state-machine information and live results. It shall label cached values with their timestamp and validity.

### 15.3 State-dependent enablement

A control shall be enabled only when:

- the capability is available;
- the current state satisfies preconditions;
- required configuration is valid;
- required resources are available;
- no conflicting operation owns an exclusive resource;
- authorization and confirmation conditions are met;
- applicable interlocks are satisfied;
- the contract and installed API are synchronized.

The disabled control shall expose a reason.

### 15.4 Resource ownership

The GUI shall represent resources declared by RFDS-017 and RFDS-018, including exclusive, shareable, read-only-shareable, multiplexed, externally locked, and unsafe-for-parallel resources.

### 15.5 Default concurrency policy

Operations targeting the same session shall execute serially unless the driver explicitly declares safe concurrency.

Cross-driver concurrency shall be disabled when RFDS-018 does not prove that resources and signal paths are independent.

### 15.6 Lock visibility

The GUI shall show:

- resource owner;
- owning operation;
- acquisition time;
- expected release condition;
- stale-lock recovery path.

The GUI shall not allow a normal operator to force-release a live hardware lock without an approved recovery workflow.

---

## 16. Invocation and Operation Lifecycle

### 16.1 Non-blocking UI

Hardware and Robot Framework execution shall not run on the presentation thread. The GUI shall remain responsive during connection, measurement, file transfer, calibration, reset, acquisition, and teardown operations.

### 16.2 Operation request

Each operation request shall include at least:

- unique correlation identifier;
- timestamp;
- driver instance and session alias;
- capability identifier and public keyword;
- exact arguments after conversion;
- profile and mode;
- operator or automation origin when available;
- required resources;
- timeout;
- expected cleanup action.

Secrets shall be redacted from evidence while remaining available to the authorized runtime.

### 16.3 Operation states

The GUI shall represent at least:

- `QUEUED`;
- `STARTING`;
- `RUNNING`;
- `WAITING_FOR_DEVICE`;
- `WAITING_FOR_OPERATOR`;
- `STOP_REQUESTED`;
- `RECOVERING`;
- `SUCCEEDED`;
- `FAILED`;
- `CANCELLED`;
- `ABORTED`;
- `TIMED_OUT`;
- `UNKNOWN_OUTCOME`.

### 16.4 Success

An operation shall be shown as successful only when the declared completion condition is met. If cleanup is mandatory, the GUI shall display operation result and cleanup result separately.

### 16.5 Unknown outcome

When communication is lost after transmission and the physical result cannot be determined, the status shall be `UNKNOWN_OUTCOME`, not success or failure by assumption. Dependent active controls shall remain blocked until recovery or state verification.

### 16.6 Retry

The GUI shall not invent retry behaviour. It shall follow the driver’s declared retry policy or invoke an approved recovery workflow.

Every retry shall be visible in evidence and shall not erase the original failure.

### 16.7 Timeout

Every blocking operation shall have a finite timeout. A GUI timeout shall not be treated as proof that the device stopped or that an output is safe.

---

## 17. Stop, Abort, Cancellation, and Application Exit

### 17.1 Capability-aware stop

A Stop or Cancel control shall be offered only when the running operation or associated workflow declares a supported stop, abort, or cancellation path.

The GUI shall not claim that a Python future, worker thread, or subprocess cancellation has stopped the physical device unless the driver or bench confirms it.

### 17.2 Stop priority

A declared stop, abort, safe-state, or emergency operation shall use a priority path that is not indefinitely blocked behind normal queued work.

### 17.3 Stop result

The GUI shall distinguish:

- stop requested;
- stop command sent;
- operation terminated;
- cleanup completed;
- safe state verified;
- safe state not independently verified.

### 17.4 Closing the GUI

When the operator closes the GUI while sessions or operations are active, the GUI shall:

1. identify active operations and hazardous states;
2. execute the approved stop and safe-teardown workflow where possible;
3. wait only within declared finite timeouts;
4. preserve evidence;
5. warn when safe state cannot be confirmed;
6. release sessions and locks deterministically.

The application shall not silently terminate while leaving a known controllable hazardous output active.

---

## 18. Manual Operator Mode

### 18.1 Scope

Manual mode may expose eligible capabilities for setup, diagnostics, development, maintenance, and supervised operation.

### 18.2 Guardrails

Manual mode shall not bypass:

- RFDS-017 preconditions;
- RFDS-018 topology and bench limits;
- authorization policy;
- resource locks;
- confirmation requirements;
- safe-state and cleanup requirements;
- evidence capture.

### 18.3 Read-back

When a set or action capability has a declared read-back operation, the GUI should offer or automatically execute read-back according to policy and display requested versus confirmed values separately.

### 18.4 Repeated and bulk actions

Repeated, ramped, scanned, or multi-channel actions shall use an approved driver capability or workflow. The GUI shall not synthesize an unbounded loop over a single active keyword without explicit rate, limit, stop, and cleanup controls.

### 18.5 Expert console

A raw SCPI, serial, frame, SDK, or arbitrary Python console shall not be part of the normal generic GUI contract.

An engineering console, when provided, shall be:

- disabled by default;
- separately authorized;
- clearly outside generic capability guarantees;
- fully logged;
- constrained by bench safety policy;
- excluded from claims that all actions use the stable semantic public API.

---

## 19. Robot Framework Test and Workflow Execution

### 19.1 Canonical execution

Robot Framework suites shall be executed through a supported Robot Framework entry point. The GUI shall preserve Robot Framework exit status and standard artifacts.

### 19.2 Inputs

Before execution, the GUI shall validate:

- selected suite or example;
- test profile;
- variables and variable files;
- tags and test selection;
- required drivers and versions;
- RFDS-018 bench contract when applicable;
- resource availability;
- safety limits;
- operator actions;
- output directory.

### 19.3 Progress

The GUI shall show determinate progress only when a reliable total and completed count are available. Otherwise it shall show an indeterminate running state plus current suite, test, keyword, phase, or operation when available.

### 19.4 Failure handling

The GUI shall preserve the original Robot Framework failure and separately report teardown, cleanup, report-generation, or export failures.

### 19.5 Result authority

Robot Framework PASS/FAIL and declared verification oracles shall remain authoritative. The GUI shall not reinterpret a failed test as passed or invent a pass threshold not present in the approved suite or contract.

### 19.6 Packaged examples

Packaged examples shall be selectable by number or filename where the driver package supports generic example runners. Prerequisites and hardware mode shall be visible before execution.

---

## 20. RFDS-018 Bench Integration

### 20.1 Required contract

A GUI controlling more than one physical driver in a defined bench shall load the deployed `system_ai_contract.yaml`.

A template stored in a driver package shall not be treated as authoritative knowledge of actual wiring, DUT connections, safety interlocks, or resource assignments.

### 20.2 Topology presentation

The GUI shall present enough topology to identify:

- devices and roles;
- DUT interfaces;
- signal producers and consumers;
- relay or multiplexer paths;
- preferred measurement sources;
- shared and exclusive resources;
- safety zones;
- operator reconfiguration points.

### 20.3 Scheduling

The GUI shall enforce declared:

- driver ordering;
- stabilization rules;
- resource conflicts;
- maximum simultaneous operations;
- parallel-execution limits;
- routing prerequisites.

### 20.4 Operator actions

An operator action shall be represented as an explicit workflow state containing:

- required action;
- reason;
- affected hardware or connection;
- prerequisite safe state;
- expected confirmation or observation;
- timeout or suspension policy;
- evidence required;
- allowed next steps.

The GUI shall not silently mark a physical operator action complete.

### 20.5 Bench mismatch

If discovered drivers, versions, identities, or resources do not match the deployed bench contract, the GUI shall block affected active workflows and present the mismatch.

---

## 21. Safety, Interlocks, and Emergency Workflow

### 21.1 Safety source

Safety rules shall be taken from RFDS-017, RFDS-018, approved device-specific requirements, and deployed configuration. Presentation hints shall never weaken them.

### 21.2 Safe defaults

The GUI shall start with:

- no unrequested active outputs;
- no automatic destructive operation;
- no implicit full-control profile;
- no silent reuse of stale hazardous state;
- concurrency disabled unless proven safe;
- simulation and real hardware clearly differentiated.

### 21.3 Limits

Applicable voltage, current, power, temperature, pressure, speed, relay topology, resistance, duration, file, calibration, and other limits shall be visible before execution and enforced at the responsible layer.

The GUI shall display the effective limit and its source.

### 21.4 Forbidden sequences

The GUI shall prevent known forbidden sequences where it has enough information to do so. The driver or bench shall still enforce them at the authoritative layer where practical.

### 21.5 Confirmation

Confirmation shall be proportional to risk. A confirmation for a significant action shall identify:

- exact operation;
- target device/session/channel;
- requested value and unit;
- relevant side effect or persistence;
- applicable limit;
- required cleanup or rollback;
- whether independent verification is available.

A generic “Are you sure?” dialog is insufficient for high-risk, persistent, calibration-changing, firmware-changing, or destructive operations.

### 21.6 Emergency control

When RFDS-018 defines an emergency workflow, the GUI shall provide a continuously accessible emergency control while the affected bench is active.

The emergency control shall:

- invoke the declared workflow, not merely close the GUI;
- have priority over normal queued work;
- report each emergency step;
- show acknowledgement and verification separately;
- remain usable from all primary operating views;
- not depend on completion of the normal test sequence.

### 21.7 Unverified safe state

If safe state cannot be independently confirmed, the GUI shall state this explicitly and show the required external action, such as removing energy, using a hardware emergency stop, or inspecting the fixture.

---

## 22. Authorization and Operating Profiles

### 22.1 Roles

A deployment requiring access control should support at least these interoperable role concepts:

- **VIEWER** — view status, results, and non-sensitive diagnostics;
- **OPERATOR** — execute approved normal workflows and permitted manual controls;
- **ENGINEER** — edit engineering profiles, run advanced diagnostics, and access controlled maintenance actions;
- **ADMINISTRATOR** — manage users, plugins, deployment policy, and protected configuration.

Equivalent role names are permitted when their permissions are documented.

### 22.2 No safety override by role

Authorization permits access but shall not override driver or bench safety constraints.

### 22.3 Operating profiles

The GUI shall support explicit operating profiles such as:

- metadata or inventory;
- simulator;
- read-only hardware;
- safe connected hardware;
- approved production workflow;
- explicit destructive or maintenance opt-in.

Profile names may differ, but privileges and risks shall be explicit.

### 22.4 Destructive operations

Firmware update, calibration write, factory reset, persistent-memory change, file deletion, security change, or equivalent destructive operations shall require:

- an explicit opt-in profile;
- authorization;
- device and compatibility verification;
- backup or recovery plan where applicable;
- stable power and connection prerequisites where applicable;
- detailed confirmation;
- dedicated evidence;
- post-operation verification.

They shall not run as part of a generic unattended batch unless the bench and workflow explicitly authorize them.

---

## 23. Configuration Management

### 23.1 Separation

The GUI shall separate:

- driver defaults;
- user profile values;
- bench-specific values;
- runtime overrides;
- discovered live state;
- secrets.

### 23.2 Precedence

Configuration precedence shall be documented and displayed. The GUI shall be able to export the effective configuration with secrets redacted.

### 23.3 Schema validation

Import and edit operations shall validate structure, types, enums, units, ranges, required fields, unknown fields, and version compatibility before application.

### 23.4 Preview and diff

Before applying a configuration that changes hardware or persistent state, the GUI shall show:

- changed fields;
- old and new values;
- units;
- affected devices or channels;
- persistence;
- operations that will be invoked;
- validation warnings;
- required restart, reconnect, or cleanup.

### 23.5 Transaction and rollback

When the driver supports transactional apply or rollback, the GUI shall use it. When updates are sequential and non-transactional, the GUI shall state that partial application is possible and shall record per-step status.

### 23.6 Unsafe and secret data

Configuration files packaged with the driver or GUI shall not contain real credentials, private resource inventories, personal local paths, or unsafe active defaults.

Secrets shall not appear in logs, reports, screenshots, clipboard exports, or diagnostic bundles.

### 23.7 Unknown fields

Unknown fields shall be handled according to the approved configuration policy. They shall not be silently dropped during round-trip export when preservation is required, and they shall not be applied as device settings without validation.

---

## 24. Measurements, Tables, Plots, and Streaming Data

### 24.1 Measurement display

Each displayed measurement should include, when available:

- value;
- unit;
- source driver and channel;
- acquisition timestamp;
- status or validity;
- range or mode;
- uncertainty or tolerance only when declared;
- raw versus processed classification.

### 24.2 No invented precision

The GUI shall not display more precision than the driver result or declared presentation policy supports in a way that implies additional accuracy.

### 24.3 Requested versus actual values

Setpoints, read-back values, measured values, calculated values, and acceptance thresholds shall be visually distinguishable.

### 24.4 Streaming

Streaming or polling shall use declared timing, throughput, and concurrency limits. The GUI shall implement backpressure, buffering, or down-sampling where necessary to remain responsive.

Loss, dropped samples, late data, or down-sampling shall be visible and recorded.

### 24.5 Raw-data preservation

Display down-sampling shall not overwrite or replace authoritative raw data when the workflow requires raw evidence.

### 24.6 Plot axes and units

Plots shall label axes and units, identify series sources, and preserve the distinction between measured and calculated data. Logarithmic axes shall reject or explicitly handle invalid non-positive values.

---

## 25. Logging, Evidence, and Audit Trail

### 25.1 Operational log

The GUI shall log at least:

- application startup and shutdown;
- driver discovery and loading;
- contract and version validation;
- connection attempts and identity results;
- state transitions;
- operation requests and arguments with secrets redacted;
- results and return schemas;
- errors, timeouts, retries, and recovery;
- operator confirmations and actions;
- resource-lock acquisition and release;
- stop, abort, emergency, and cleanup results;
- configuration imports, diffs, and exports;
- Robot run start, completion, and artifact locations.

### 25.2 Correlation

Every operation, error, result, and protocol or Robot evidence reference shall carry a correlation identifier sufficient to reconstruct the sequence.

### 25.3 Version evidence

Each GUI session or Robot run shall record, as applicable:

- GUI version;
- driver package and library versions;
- RFDS-017 contract version and lock/hash;
- RFDS-018 bench contract version/hash;
- Python and Robot Framework versions;
- operating system;
- selected profile;
- simulator identity or device model, serial number, and firmware;
- effective configuration with secrets redacted;
- test-suite or example version;
- qualification status.

### 25.4 Recommended result layout

```text
results/gui/<bench_or_standalone>/<timestamp>/
├── gui_session.json
├── operation_events.jsonl
├── errors.jsonl
├── driver_inventory.json
├── device_identity.json
├── contract_versions.json
├── effective_configuration.json
├── resource_locks.jsonl
├── safety_and_cleanup.json
├── measurements.csv
├── attachments/
└── robot/
    ├── output.xml
    ├── log.html
    ├── report.html
    └── additional_robot_evidence/
```

Files that do not apply may be omitted, but the session summary shall state why.

RFDS-008 §11 is the sole normative source for the canonical result-directory layout and artifact roles. The GUI-specific layout above is an illustrative mapping onto that canonical layout (for example, `gui_session.json` corresponds to RFDS-008's `run_summary.json`, and `operation_events.jsonl` corresponds to RFDS-008's `events/operations.jsonl`); a GUI implementation may instead write directly into the RFDS-008 canonical paths, and shall do so when both are produced for the same run to avoid duplicate, divergent evidence roots.

### 25.5 Diagnostic bundle

The GUI shall provide a deterministic diagnostic-bundle export containing relevant logs, versions, sanitized configuration, identities, errors, and evidence references without secrets.

---

## 26. Error and Diagnostic Presentation

### 26.1 Error categories

The GUI shall preserve the driver’s documented error category and distinguish, where applicable:

- validation;
- state or precondition;
- resource conflict;
- authorization;
- safety or interlock;
- transport;
- protocol;
- timeout;
- device-reported error;
- unsupported operation;
- configuration;
- operator-action timeout;
- cleanup;
- internal GUI or adapter failure.

### 26.2 Error content

An operator-facing error shall provide:

- concise summary;
- affected device/session/capability;
- whether transmission occurred when known;
- current or uncertain state;
- actionable recovery steps;
- evidence or diagnostic reference;
- safe-state status.

Technical details and original cause shall remain available in diagnostics.

### 26.3 No silent success

The GUI shall never convert a failed required operation into success because a retry, reconnect, or cleanup later succeeded.

### 26.4 Error queue and device status

When the device exposes an error queue, status register, health query, or self-test, the GUI shall present it through the public capability and shall not parse raw protocol responses itself.

### 26.5 Recovery

Recovery controls shall be derived from documented recovery actions. The GUI shall not suggest “Retry” when the operation is not safe to repeat.

---

## 27. Responsiveness, Timing, and Reliability

### 27.1 Presentation responsiveness

The presentation event loop shall not perform blocking hardware, file, network, Robot Framework, or report-generation work.

### 27.2 Polling

Polling intervals shall respect declared device timing and bus limits. Polling shall pause, reduce, or serialize when it conflicts with active operations.

### 27.3 Refresh age

Displayed live state shall include age or stale indication when refresh is not continuous.

### 27.4 Worker failure

Unexpected worker, subprocess, or adapter failure shall:

- mark affected operations failed or unknown;
- release only locks proven safe to release;
- preserve evidence;
- trigger declared recovery or safe-state workflow;
- avoid crashing unrelated driver sessions where practical.

### 27.5 Restart recovery

A production GUI should detect an incomplete previous session and offer evidence review and state resynchronization. It shall not assume previous teardown succeeded.

### 27.6 System sleep and network changes

Where relevant, the GUI shall detect host sleep, resume, network-interface changes, USB removal, or lost remote sessions and transition affected devices to degraded or unknown state.

---

## 28. Security Requirements

### 28.1 Untrusted input

The GUI shall treat device strings, logs, imported configuration, contract files, result files, and plugin metadata as untrusted input.

### 28.2 Rendering

HTML, Markdown, rich text, terminal escapes, and file paths shall be sanitized before rendering or opening.

### 28.3 Plugin trust

Only approved and identifiable driver plugins shall be loaded. Plugin installation or enablement shall require appropriate authorization and shall be recorded.

### 28.4 File operations

Upload, download, export, and delete operations shall validate paths, filenames, size, type, destination, overwrite policy, and integrity where applicable.

The GUI shall not execute imported files or shell content merely because they were provided by a driver or device.

### 28.5 Remote GUIs

A network-accessible GUI shall use authenticated sessions, authorization, transport protection appropriate to the deployment, session timeout, and protection against cross-site or command-injection risks.

### 28.6 Secret management

Credentials and tokens shall be stored using an approved secret mechanism, not plaintext GUI profiles or source-controlled files.

---

## 29. Accessibility, Localization, and Operator Usability

### 29.1 Accessibility

A production GUI shall:

- support keyboard operation for essential controls;
- provide accessible labels and focus order;
- avoid conveying status by colour alone;
- expose text equivalents for icons and plots where practical;
- maintain readable contrast and scalable text;
- provide confirmation and error text that identifies the affected operation.

### 29.2 Localization

Operator-facing text may be localized, but machine-readable evidence shall use stable identifiers, UTF-8, ISO 8601 timestamps, and locale-neutral numeric serialization.

### 29.3 Terminology

The GUI shall use driver and bench terminology consistently. It shall not rename a physical concept in a way that changes its meaning.

### 29.4 Dangerous control placement

Emergency controls shall remain accessible. Destructive controls shall not be placed adjacent to routine controls without separation, distinct labelling, and confirmation.

### 29.5 Status clarity

The GUI shall show at least these distinctions where applicable:

- connected versus verified;
- simulated versus hardware;
- requested versus confirmed;
- running versus waiting for operator;
- failed versus cleanup failed;
- safe command issued versus safe state verified;
- cached versus live value;
- qualified versus unverified capability.

---

## 30. Device-Specific GUI Extensions

### 30.1 Permitted extensions

A driver may provide an optional device-specific panel for complex features such as:

- waveform viewing;
- oscilloscope screenshots;
- scanner topology;
- calibration tables;
- relay matrices;
- chamber profiles;
- firmware management;
- advanced file systems;
- vendor-specific diagnostics.

### 30.2 Extension boundary

An extension shall use the same invocation gateway and public capabilities as the generic GUI. It shall not receive privileged access to private driver or transport objects.

### 30.3 Fallback

Failure to load an optional extension shall not prevent generic metadata, lifecycle, diagnostics, and eligible capability access.

### 30.4 No semantic override

An extension may provide richer presentation but shall not override contract limits, preconditions, risk, resources, timeout, error, or cleanup semantics.

### 30.5 Version compatibility

Extensions shall declare compatible GUI API, driver package, and contract versions. An incompatible extension shall be disabled with a visible reason.

---

## 31. Required GUI Integration Artifacts

A driver claiming GUI-L2 or higher shall provide equivalent artifacts to:

```text
rf_<driver_name>/
├── generated/
│   └── gui_manifest/
│       └── driver_gui_manifest.json
├── tests/
│   └── gui_integration/
│       ├── test_manifest_generation.py
│       ├── test_control_projection.py
│       ├── test_invocation_mapping.py
│       └── gui_integration.robot
├── docs/
│   └── gui_integration.md
└── review/
    └── <version>_gui_integration_review.md
```

Equivalent locations are permitted until RFDS-005 is revised, provided they are documented and included in release validation.

### 31.1 Generated GUI manifest

`driver_gui_manifest.json` shall be generated from authoritative sources and shall not become an independent source of semantic truth.

It shall contain at least:

- source package and contract versions;
- source hashes;
- driver identity;
- supported GUI compatibility level;
- connection profiles;
- projected capability inventory;
- input and output schemas;
- state and resource references;
- qualification status;
- presentation hints;
- generation timestamp and tool version.

### 31.2 Drift validation

The build shall fail when the generated GUI manifest does not match the current public API and RFDS-017 contract.

### 31.3 Documentation

`docs/gui_integration.md` shall describe:

- compatibility level;
- generic controls available;
- connection profiles;
- manual and Robot execution behaviour;
- safety and operator actions;
- unsupported or workflow-only capabilities;
- extension panels;
- evidence output;
- known GUI limitations.

---

## 32. GUI Integration Test Requirements

### 32.1 Static and schema tests

Tests shall verify:

- RFDS-017 and RFDS-018 validation;
- contract lock and version consistency;
- GUI-manifest schema validation;
- complete public capability inventory;
- no unsupported private symbols;
- deterministic manifest generation;
- presentation hints do not alter authoritative semantics.

### 32.2 Control-projection tests

For every projected capability, tests shall verify:

- control type;
- argument order;
- required and optional handling;
- default and omission semantics;
- enum values;
- units and limits;
- state-dependent enablement;
- unavailable reason;
- return-value rendering.

### 32.3 Invocation tests

Every enabled generic control shall be tested through the public invocation path using a deterministic simulator or approved fake.

Tests shall verify:

- exact capability mapping;
- exact argument values;
- session targeting;
- timeout;
- structured result;
- error mapping;
- evidence correlation;
- cleanup request.

### 32.4 Negative tests

Tests shall cover, as applicable:

- stale contract;
- API signature mismatch;
- missing safety data;
- unknown input type;
- invalid value;
- illegal state;
- unavailable resource;
- lock conflict;
- unsupported role/profile;
- timeout;
- lost connection;
- malformed return value;
- cleanup failure;
- extension failure;
- unsafe configuration import.

### 32.5 Responsiveness tests

Tests shall verify that long-running operations, connection attempts, large result rendering, and report generation do not block the presentation event loop beyond the approved responsiveness threshold.

### 32.6 Stop and recovery tests

Tests shall verify:

- stop availability only when supported;
- priority routing;
- timeout behaviour;
- unknown-outcome handling;
- recovery;
- subsequent valid operation;
- safe cleanup.

### 32.7 Robot execution tests

Tests shall verify:

- suite selection;
- variable validation;
- output directory creation;
- exit-code preservation;
- standard Robot artifacts;
- live status mapping;
- failure and teardown separation;
- stop behaviour.

### 32.8 Bench tests

GUI-L4 tests shall use an RFDS-018 test bench or approved deterministic bench simulator to verify topology, operator actions, resource conflicts, sequencing, stabilization, emergency workflow, and safe shutdown.

### 32.9 HIL tests

Before GUI-L5 production claim, representative real-hardware tests shall verify at least:

- connect and identity;
- one read-only operation per major capability group;
- one reversible configuration operation per applicable group;
- representative active operation under declared limits;
- stop or abort where supported;
- connection-loss or timeout recovery where safe;
- teardown and safe-state result;
- evidence generation.

### 32.10 Accessibility and security tests

Production review shall include keyboard operation, non-colour status identification, focus behaviour, input sanitization, secret redaction, unauthorized action rejection, and safe file handling.

---

## 33. GUI Integration Coverage Matrix

The release review shall include a matrix containing at least:

| Field | Requirement |
|---|---|
| Capability | Public keyword/capability identifier |
| Canonical keyword | Canonical public operation |
| GUI status | Primary, advanced, workflow-only, read-only, unavailable, deprecated |
| Input projection | PASS/FAIL/N/A |
| Output projection | PASS/FAIL/N/A |
| State gating | PASS/FAIL/N/A |
| Resource gating | PASS/FAIL/N/A |
| Authorization | PASS/FAIL/N/A |
| Safety confirmation | PASS/FAIL/N/A |
| Invocation mapping | PASS/FAIL/N/A |
| Simulator tested | PASS/FAIL/N/A |
| HIL tested | PASS/FAIL/N/A |
| Stop/recovery tested | PASS/FAIL/N/A |
| Evidence generated | PASS/FAIL |
| RFDS-019 status | Qualified, partial, excluded, unverified |
| Result | PASS/FAIL/SKIP/EXCLUDED |
| Reason | Required for SKIP or EXCLUDED |
| Evidence | Test/report reference |

Aliases shall remain visible as separate inventory rows or traceable compatibility entries.

### 33.1 Coverage metrics

The report shall calculate at least:

```text
GUI Inventory Coverage
  = GUI-inventoried public capabilities / exported public capabilities

Control Projection Coverage
  = projected eligible capabilities / GUI-eligible capabilities

Invocation Coverage
  = simulator-invoked projected capabilities / projected executable capabilities

State-Gating Coverage
  = state-tested capabilities / state-dependent capabilities

Safety-Gating Coverage
  = safety-tested active capabilities / active GUI capabilities

HIL GUI Coverage
  = hardware-tested GUI capabilities / hardware-applicable GUI capabilities
```

Skipped and excluded entries shall remain visible.

---

## 34. Acceptance Criteria

A GUI integration passes RFDS-012 only when all applicable criteria pass.

1. 100% of exported public capabilities are inventoried or explicitly classified.
2. No normal GUI control invokes a private method, transport primitive, or handcrafted protocol operation.
3. The installed public API, RFDS-017 contract, and generated GUI manifest are version-consistent.
4. Every enabled control maps to the exact declared public capability and argument semantics.
5. Required inputs, defaults, omission, enums, limits, and units are represented correctly.
6. Capability enablement follows declared state, resource, authorization, and safety preconditions.
7. Missing or contradictory safety-critical information causes fail-closed behaviour.
8. Simulation and hardware modes are visibly distinct, with no silent fallback.
9. Blocking driver and Robot operations do not block the presentation thread.
10. All blocking operations have finite timeouts.
11. Stop, abort, retry, and recovery are offered only according to declared behaviour.
12. Unknown physical outcome is represented explicitly.
13. Multi-driver operation uses the deployed RFDS-018 contract.
14. Resource conflicts and unsafe parallel operations are prevented.
15. Emergency workflow remains accessible and reports acknowledgement versus verification.
16. Configuration import is schema-validated and active changes use a preview or guided workflow.
17. Secrets are redacted from display, logs, evidence, and diagnostic bundles.
18. Robot Framework exit status and standard reports are preserved.
19. Every operator action and operation is traceable through correlation identifiers and version evidence.
20. RFDS-019 qualification status is displayed without overstating simulator or HIL evidence.
21. Safe teardown is attempted on failure and application exit, and its result is recorded.
22. Generic fallback remains usable when an optional device-specific extension fails.
23. Required GUI integration tests pass.
24. Required documentation, history, review, and release evidence are current.
25. No Critical finding remains open; Major findings are corrected or formally accepted with visible residual risk.

---

## 35. Failure Conditions

RFDS-012 shall fail when any of the following applies:

- a public capability is silently omitted;
- the GUI uses private driver methods or direct protocol/transport access;
- vendor or model checks replace capability discovery for generic behaviour;
- the GUI and driver contract versions are stale or contradictory but active controls remain enabled;
- an unknown safety limit is guessed;
- an unsupported input type is accepted through an unrestricted active-operation field;
- argument omission, default, unit, range, or enum semantics are changed;
- a control remains enabled in an illegal state or during a resource conflict;
- simulation is silently substituted after real-hardware failure;
- a worker blocks the presentation event loop;
- an operation can wait indefinitely without an approved interrupt mechanism;
- GUI cancellation is represented as physical stop without confirmation;
- a timeout is represented as safe device state;
- an active operation lacks declared cleanup or an approved exclusion;
- an emergency control merely closes the GUI;
- RFDS-018 topology or operator action is assumed but not declared;
- configuration changes are applied without validation;
- a destructive operation runs without explicit profile, authorization, and confirmation;
- secrets appear in logs, reports, screenshots, or exports;
- Robot Framework failure is hidden or reclassified as success;
- operation evidence lacks driver, device, capability, arguments, time, result, or cleanup correlation;
- the GUI claims physical verification based only on command completion or simulation;
- an optional extension bypasses the invocation gateway or weakens safety semantics;
- mandatory simulator, HIL, safety, or recovery tests are missing for the claimed compatibility level.

---

## 36. Lifecycle Integration

RFDS-012 shall be implemented through the RFDS phase-and-gate lifecycle.

### 36.1 Gate 1 — Architecture and Skeleton

Deliverables:

- GUI integration architecture;
- invocation gateway interface;
- contract and manifest loaders;
- operation and state models;
- driver/plugin discovery design;
- evidence directory design;
- threat and safety boundary review;
- buildable metadata-only GUI.

Acceptance:

- GUI-L0 target supported;
- no hardware access during discovery;
- public/private boundary documented;
- no Critical architecture finding.

### 36.2 Gate 2 — Core Implementation

Deliverables:

- connection and identity workflow;
- generic control generation;
- input validation;
- asynchronous operation execution;
- structured result and error mapping;
- basic logging and diagnostics;
- simulator tests.

Acceptance:

- GUI-L1 and planned GUI-L2 core workflows operate;
- primary controls invoke exact public capabilities;
- unit and integration tests pass.

### 36.3 Gate 3 — Extended Features

Deliverables:

- Robot execution;
- multi-session support;
- configuration import/export;
- resource locking;
- advanced data visualization;
- authorization profiles;
- optional extension API;
- stop, recovery, and restart handling;
- RFDS-018 bench integration where in scope.

Acceptance:

- feature-complete for the phase;
- safety and resource rules enforced;
- API remains backward compatible or migration is documented.

### 36.4 Gate 4 — Tests and Documentation

Deliverables:

- full static, simulator, GUI, Robot, negative, recovery, accessibility, and security tests;
- HIL tests where applicable;
- GUI integration coverage matrix;
- user and deployment guides;
- updated README and GitHub Pages;
- troubleshooting and evidence guide.

Acceptance:

- all mandatory tests pass;
- documentation matches the released GUI and driver versions;
- examples are runnable;
- remaining hardware gaps are explicit.

### 36.5 Gate 5 — Review and Release

Deliverables:

- functional review;
- architecture review;
- GUI/API boundary review;
- safety review;
- security review;
- accessibility review;
- Robot execution review;
- documentation review;
- regression review;
- release-readiness review;
- history entry, release notes, and package.

Acceptance:

- claimed GUI compatibility level is evidenced;
- no Critical issue remains;
- Major issues are resolved or formally accepted;
- release versions and contracts are consistent.

---

## 37. Change Control

Whenever a public capability, state, input, output, limit, resource, error, retry, timeout, safety rule, cleanup action, connection profile, or qualification status changes, the same revision shall update, as applicable:

- RFDS-017 contract and lock;
- RFDS-018 bench references;
- public API manifest;
- generated GUI manifest;
- control-projection tests;
- invocation tests;
- safety and state-gating tests;
- GUI documentation;
- device-specific extension compatibility;
- examples and Robot workflows;
- history and review evidence;
- release notes and migration guidance.

A presentation-only change shall not require semantic contract changes, but shall still be tested for accessibility, safety visibility, and compatibility.

A breaking GUI extension or manifest-schema change shall provide versioning and migration guidance.

---

## 38. Review Checklist

1. Does the GUI load drivers from declared capabilities instead of vendor/model branching?
2. Does every normal control use the public invocation gateway?
3. Are all public capabilities inventoried?
4. Are contract, package, API manifest, and GUI manifest versions consistent?
5. Does metadata discovery avoid hardware access?
6. Are simulation and hardware modes unmistakable?
7. Are connection and identity states distinguished?
8. Are session aliases explicit?
9. Are arguments, defaults, omission, units, enums, and limits projected correctly?
10. Are unknown or unsupported types handled safely?
11. Are preconditions and current state reflected in control enablement?
12. Does every disabled control provide a reason?
13. Are resource locks and concurrency rules enforced?
14. Does the GUI remain responsive during blocking operations?
15. Are all timeouts finite?
16. Is stop or cancel shown only when supported?
17. Is unknown physical outcome represented explicitly?
18. Are requested, read-back, and independently measured values distinguished?
19. Is RFDS-018 loaded for multi-driver hardware operation?
20. Are operator actions explicit and evidenced?
21. Are safety limits and their sources visible?
22. Are forbidden sequences blocked where possible?
23. Is emergency control continuously accessible and priority-routed?
24. Are destructive actions separately authorized and confirmed?
25. Does configuration import validate and preview changes?
26. Are partial non-transactional updates visible?
27. Are secrets redacted everywhere?
28. Are errors categorized and actionable?
29. Does recovery preserve the original failure?
30. Are Robot Framework exit status and reports preserved?
31. Are logs and evidence correlated to operations and versions?
32. Is simulator evidence distinguished from HIL evidence?
33. Do optional extensions preserve the public-API and safety boundary?
34. Do accessibility and localization checks pass?
35. Do simulator, negative, recovery, and representative HIL tests pass for the claimed level?
36. Are documentation, history, reviews, and release notes current?
37. Are all Critical findings closed?
38. Are Major findings corrected or formally accepted with residual risk?

---

## 39. Minimum Definition of Done

RFDS-012 is complete for a driver/GUI integration when:

- the target GUI compatibility level is declared;
- the public capability inventory is complete;
- RFDS-017 and, where applicable, RFDS-018 load and validate;
- contract and public API drift checks pass;
- the generated GUI manifest is current;
- eligible controls are generated and validated;
- every enabled control maps to the exact public operation;
- connection, state, resource, timeout, error, and cleanup behaviour is represented;
- manual and Robot Framework execution paths preserve safety and evidence;
- simulator and required HIL tests pass;
- multi-driver operation uses the deployed bench contract;
- safe teardown and emergency workflow are tested where applicable;
- required evidence and coverage reports are generated;
- documentation, history, and review records are current;
- all acceptance criteria in Section 34 pass.

---

## 40. Goal

Provide a stable, metadata-driven, safe, testable, and evidence-producing operator GUI integration model in which any conforming RFDS driver can be loaded and operated through its declared public capabilities without embedding device-specific protocol knowledge in the generic GUI.

---

## Appendix A — Minimal Generated GUI Manifest Example

The exact schema may be refined by RFDS-013, RFDS-014, and RFDS-015. The following example defines the required intent and is not an independent semantic authority.

```json
{
  "schema": "rfds-012-gui-manifest-1.0",
  "generated": {
    "timestamp": "2026-07-26T12:00:00Z",
    "tool_version": "1.0.0",
    "sources": {
      "driver_package": "rf_example_v26.01",
      "driver_version": "26.1",
      "rfds017_version": "3.0",
      "rfds017_hash": "<sha256>",
      "public_api_hash": "<sha256>"
    }
  },
  "identity": {
    "driver_name": "example",
    "library_name": "ExampleLibrary",
    "instrument_class": "power_supply",
    "gui_compatibility_level": "GUI-L2"
  },
  "connection_profiles": [
    {
      "id": "visa",
      "mode": "REAL_HARDWARE",
      "fields": [
        {
          "name": "resource",
          "type": "string",
          "required": true,
          "secret": false
        }
      ]
    },
    {
      "id": "simulator",
      "mode": "SIMULATOR",
      "fields": []
    }
  ],
  "capabilities": [
    {
      "id": "CAP-SET-VOLTAGE",
      "keyword": "Set DC Voltage",
      "canonical_keyword": "Set DC Voltage",
      "presentation": "PRIMARY",
      "inputs": [
        {
          "name": "channel",
          "type": "integer",
          "required": true,
          "minimum": 1,
          "maximum": 4
        },
        {
          "name": "voltage",
          "type": "number",
          "unit": "V",
          "required": true,
          "minimum": 0.0,
          "maximum": 20.0
        }
      ],
      "return": {
        "type": "null"
      },
      "preconditions": ["CONNECTED_VERIFIED", "OUTPUT_SAFE_TO_CONFIGURE"],
      "risk_reference": "RFDS017:CAP-SET-VOLTAGE",
      "resources": ["psu_session", "channel:<channel>"],
      "timeout_s": 10,
      "cleanup_reference": "RFDS017:CAP-DISABLE-OUTPUT",
      "qualification": {
        "rfds019": "QUALIFIED",
        "hil": "VERIFIED"
      }
    }
  ]
}
```

---

## Appendix B — Standard GUI Operation Event Example

```json
{
  "correlation_id": "op-20260726-000123",
  "timestamp": "2026-07-26T12:03:45.126Z",
  "origin": "OPERATOR",
  "driver": "rf_example",
  "driver_version": "26.1",
  "session_alias": "PSU_MAIN",
  "capability_id": "CAP-SET-VOLTAGE",
  "keyword": "Set DC Voltage",
  "arguments": {
    "channel": 1,
    "voltage": 5.0
  },
  "profile": "SAFE_CONNECTED",
  "mode": "REAL_HARDWARE",
  "state": "SUCCEEDED",
  "result": null,
  "duration_s": 0.246,
  "cleanup": {
    "required": false,
    "status": "NOT_APPLICABLE"
  },
  "evidence": {
    "robot_test": null,
    "protocol_trace": "rfds019://CAP-SET-VOLTAGE/vector-01",
    "log_reference": "operation_events.jsonl:124"
  }
}
```

---

## Appendix C — Safe Control-Enablement Decision

A generic active control should use logic equivalent to:

```text
ENABLE only when:
    contract_valid
AND api_lock_valid
AND capability_available
AND input_schema_supported
AND connection_verified
AND state_preconditions_met
AND configuration_valid
AND resources_available
AND bench_topology_allows
AND limits_known_and_satisfied
AND interlocks_satisfied
AND role_authorized
AND profile_authorized
AND no_conflicting_operation
AND cleanup_defined_or_approved_exclusion

Otherwise:
    DISABLE
    show one or more explicit blocking reasons
```

The GUI may apply stricter policy. It shall not weaken any authoritative condition.

---

## Appendix D — Changes in Version 1.0

Version 1.0 establishes the initial RFDS generic GUI integration contract, including:

- metadata-driven capability projection;
- strict public-API and no-direct-protocol boundary;
- RFDS-017, RFDS-018, and RFDS-019 integration;
- generic control generation and validation;
- lifecycle, state, resource, timeout, cancellation, and recovery presentation;
- manual and Robot Framework execution modes;
- safety, operator action, emergency, authorization, and destructive-operation rules;
- configuration, logging, evidence, diagnostics, accessibility, and security requirements;
- optional device-specific extensions;
- GUI compatibility levels, testing, coverage, review, and release acceptance.
