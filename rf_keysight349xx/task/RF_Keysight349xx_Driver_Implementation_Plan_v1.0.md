# RF Keysight 349xx Robot Framework Driver — Implementation Plan

**Document version:** 1.0  
**Planned driver:** `rf_keysight349xx`  
**Target instruments:** Keysight / Agilent 34970A and 34972A  
**Target release family:** `rf_keysight349xx_v26.01.00`  
**Status:** Implementation planning specification  
**Date:** 2026-08-17  

---

## 1. Purpose

This document defines the implementation plan for a production-grade Robot Framework driver for the Keysight / Agilent 34970A and 34972A data acquisition / switch units.

The driver shall be implemented against the uploaded project RFDS specifications and the supplied Keysight/Agilent 34970A/34972A Command Reference.

The implementation shall not silently invent device capabilities or protocol behavior. Every supported public capability shall be traceable to:

1. a project RFDS requirement;
2. a documented device command or behavior;
3. a public Robot Framework keyword;
4. a protocol vector;
5. verification evidence.

Any device behavior that cannot be established from the available authoritative sources shall be marked `UNKNOWN`, `NOT_APPLICABLE`, `EXCLUDED`, or an approved deviation.

---

## 2. Authoritative Source Set

The following uploaded documents are the implementation baseline.

### 2.1 RFDS project requirements

- RFDS-001 — Platform Requirements v1.2
- RFDS-002 — Mandatory Public API and Keyword Standard v1.1
- RFDS-003 — BaseInstrumentLibrary Common Base Class Design v2.0
- RFDS-004 — Transport Layer Specification v2.0
- RFDS-005 — Driver Package Specification v1.3
- RFDS-006 — Coding Standard v1.0
- RFDS-007 — Error and Exception Standard v1.0
- RFDS-009 — Testing Standard v1.0
- RFDS-010 — Driver Review Checklist v1.0
- RFDS-012 — GUI Integration Specification v1.0
- RFDS-014 — Driver Configuration Model Specification v1.0
- RFDS-015 — Plugin Architecture v1.0
- RFDS-017 — AI Driver Contract v3.0
- RFDS-018 — AI Test Bench Contract v1.0
- RFDS-019 — Robot Framework Driver Call and Protocol Conformance Test Specification v1.1
- RFDS Driver Implementation Lifecycle v1.1

### 2.2 Device source

- Keysight / Agilent 34970A / 34972A Command Reference

This command reference is the authoritative source for device SCPI command syntax, supported models, channel behavior, module behavior, status, errors, trigger functions, measurements, and remote-control protocol behavior.

### 2.3 Project repository

Project repository:

`https://github.com/ami3go/RobotFrameworks_hw_drivers`

---

## 3. Driver Identity

The driver shall be implemented as a family driver.

### 3.1 Canonical identity

```text
Project/root:       rf_keysight349xx/
Python import:      rf_keysight349xx
Distribution:       rf-keysight349xx
Plugin ID:          keysight.349xx
Robot library:      rf_keysight349xx.library
```

### 3.2 Package naming

Release ZIP:

```text
rf_keysight349xx_v26.01.00.zip
```

Gate builds:

```text
rf_keysight349xx_v26.01.00-g1.zip
rf_keysight349xx_v26.01.00-g2.zip
rf_keysight349xx_v26.01.00-g3.zip
rf_keysight349xx_v26.01.00-g4.zip
rf_keysight349xx_v26.01.00-g5.zip
```

The ZIP shall contain exactly one stable package root:

```text
rf_keysight349xx/
```

---

## 4. Supported Instrument Family

### 4.1 Mainframes

Planned support:

- Keysight / Agilent 34970A
- Keysight 34972A

### 4.2 Model-specific behavior

The driver shall not assume both models support the same interfaces or commands.

Expected distinction:

```text
34970A
├── GPIB
└── RS-232

34972A
├── LAN
├── USB / VISA
└── 34972A-specific LAN and memory functionality
```

The driver shall determine the connected model using `*IDN?`.

### 4.3 Module discovery

During connection the driver shall discover installed modules in slots:

```text
100
200
300
```

Module discovery shall be used to construct the effective runtime capability model.

Supported card families are expected to include:

- 34901A
- 34902A
- 34903A
- 34904A
- 34905A
- 34906A
- 34907A
- 34908A

Support for each card shall be marked separately as:

- implemented;
- simulator tested;
- hardware tested;
- excluded;
- unknown.

---

## 5. Top-Level Architecture

```text
Robot Framework
      │
      ▼
library.py
RFDS canonical public API
      │
      ▼
BaseInstrumentLibrary
RFDS lifecycle / sessions / timeout /
locking / evidence / errors
      │
      ▼
core/
device semantics
      │
      ▼
protocol/
SCPI generation + response parsing
      │
      ▼
RFDS transport interface
      │
      ├── VISA
      ├── Serial
      ├── TCP/LAN
      └── Simulator / protocol spy
             │
             ▼
       34970A / 34972A
```

### 5.1 Architectural requirements

The implementation shall:

- derive from the approved `BaseInstrumentLibrary`;
- perform zero hardware I/O during module import;
- perform zero hardware I/O during library construction;
- disable uncontrolled automatic Robot Framework keyword exposure;
- expose only intentional public keywords;
- use the RFDS transport abstraction;
- keep protocol serialization separate from transport;
- keep device semantics separate from Robot Framework adapters;
- guarantee finite blocking behavior;
- clean up partial connection attempts;
- produce observable protocol evidence;
- avoid unsafe implicit retries.

---

## 6. Connection Workflow

Connection sequence:

```text
Open selected transport
      ↓
Query *IDN?
      ↓
Parse manufacturer / model / serial / firmware
      ↓
Validate supported mainframe
      ↓
Discover installed modules
      ↓
Discover relevant runtime state
      ↓
Build effective capability model
      ↓
Cache identity and module inventory
      ↓
Connection state = CONNECTED
```

A failed connection attempt shall:

- close opened resources;
- clear partially initialized state;
- retain useful diagnostics;
- return a normalized RFDS exception.

---

## 7. Mandatory RFDS Universal API

The driver shall implement all mandatory universal keywords:

```text
Connect
Disconnect
Is Connected
Get Connection State
Check Communication
Get Identity
Get Driver Information
Get Driver Capabilities
Set Communication Timeout
Get Communication Timeout
```

### 7.1 Semantic rules

- `Get Identity` shall normally use cached identity.
- Live refresh shall require an explicit operation.
- `Is Connected` shall not perform surprise hardware I/O.
- `Check Communication` shall perform an actual communication probe.
- Communication timeout shall always be finite.
- Return values shall be Robot Framework-compatible.
- Keyword names shall remain stable across revisions.

---

## 8. Conditional RFDS API Groups

Where the corresponding capability is implemented, the complete applicable keyword group shall also be implemented.

Expected groups include:

- multi-connection;
- device error queue;
- channel discovery and validation;
- measurement;
- switching / relay control;
- reset / preset;
- safe shutdown;
- raw protocol I/O;
- configuration;
- diagnostics.

Partial implementation of a declared RFDS capability group shall not be accepted without an approved deviation.

---

## 9. System and Identity Functions

Planned functions:

```text
Get Instrument Information
Get Installed Modules
Get Module Information
Get SCPI Version
Run Self Test
Reset Device
Preset Device
Clear Status
Get Line Frequency
```

The exact exported Robot keyword names shall be finalized in the public API contract before implementation.

---

## 10. Device Error Queue

The driver shall implement:

```text
Get Device Error
Get All Device Errors
Clear Device Errors
Device Error Queue Should Be Empty
```

### 10.1 Error handling requirements

The driver shall:

- parse `SYST:ERR?` responses strictly;
- preserve device error number and message;
- distinguish no-error from malformed response;
- raise `DriverProtocolError` for malformed error responses;
- never interpret malformed SCPI as `0,"No error"`;
- provide complete queue draining with bounded iteration;
- record device error evidence in conformance tests.

---

## 11. Measurement Engine

Planned measurement capabilities:

```text
Measure DC Voltage
Measure AC Voltage
Measure DC Current
Measure AC Current
Measure Resistance
Measure 4 Wire Resistance
Measure Frequency
Measure Period
```

For applicable measurement families the driver should also expose:

```text
Configure <Quantity>
Measure <Quantity>
Get <Quantity> Configuration
```

### 11.1 Measurement requirements

The implementation shall:

- validate channels before transmission;
- validate installed card compatibility;
- validate model restrictions;
- validate range and resolution arguments;
- return numeric values rather than raw SCPI text where practical;
- preserve unit metadata where appropriate;
- expose clear exceptions for unsupported combinations.

### 11.2 Unsupported or unverified functions

Continuity and diode measurement shall not be implemented unless an authoritative device source establishes corresponding supported behavior.

Initial disposition:

```yaml
continuity: UNKNOWN
diode: UNKNOWN
```

No substitute implementation shall be invented by mapping these functions to resistance or voltage measurements.

---

## 12. Scan and Acquisition Engine

Planned scan-related operations:

```text
Configure Scan List
Get Scan List
Clear Scan List

Configure Trigger Source
Get Trigger Source
Set Trigger Count
Get Trigger Count
Set Trigger Timer
Get Trigger Timer

Initiate Scan
Abort Scan
Read Scan
Fetch Readings
Read Buffered Readings
Get Reading Count
Clear Reading Memory
Get Scan Start Time
```

The driver shall preserve the semantic distinctions between:

```text
INITiate
FETCh?
READ?
R?
DATA:REMove?
```

These commands shall not be treated as interchangeable because they have different acquisition, buffering, and reading-memory behavior.

---

## 13. Statistics

Planned statistics functions:

```text
Get Channel Minimum
Get Channel Maximum
Get Channel Average
Get Channel Count
Get Channel Peak To Peak
Clear Channel Statistics
Get Minimum Timestamp
Get Maximum Timestamp
```

Recommended structured return format:

```python
{
    "channel": 103,
    "minimum": 1.234,
    "maximum": 1.241,
    "average": 1.237,
    "peak_to_peak": 0.007,
    "count": 100
}
```

The public API shall not leak undocumented SCPI formatting into higher-level Robot Framework tests.

---

## 14. Temperature Engine

Planned sensor support:

```text
Thermocouple
2-wire RTD
4-wire RTD
Thermistor
```

Configuration shall include applicable device settings such as:

```text
Thermocouple type
Reference junction type
Reference junction value
Thermocouple check
RTD type
RTD reference resistance
Thermistor type
Temperature units
```

### 14.1 Channel-pair validation

The implementation shall understand four-wire pairing rules for supported cards rather than treating all channel numbers as independent.

Invalid pairings shall be rejected before protocol transmission when deterministically known.

---

## 15. Switching and Routing

Planned switching functions:

```text
List Switch Channels
Open Channel
Close Channel
Open Channels
Close Channels
Get Channel State
Open All Owned Channels
Channel Should Be Open
Channel Should Be Closed
```

### 15.1 Resource ownership

The driver shall track resources owned by the current session.

It shall not assume ownership of every relay or switch channel in the mainframe.

Safe shutdown shall act only on explicitly owned resources unless the bench contract explicitly grants broader ownership.

---

## 16. 34907A Multifunction Module

The 34907A shall have a dedicated capability implementation.

### 16.1 Digital input

```text
Read Digital Byte
Read Digital Word
```

### 16.2 Digital output

```text
Write Digital Byte
Write Digital Word
Get Digital Output
Get Digital Direction
```

Digital input/output direction changes shall be represented as explicit state transitions and side effects.

### 16.3 Totalizer

```text
Start Totalizer
Stop Totalizer
Read Totalizer
Clear Totalizer
Set Totalizer Edge
Get Totalizer Edge
Set Totalizer Read Mode
```

### 16.4 DAC

```text
Set DAC Voltage
Get DAC Voltage
```

DAC operations shall be classified as state-changing and potentially safety-relevant.

Blind automatic retries shall be prohibited for uncertain state-changing DAC writes.

---

## 17. Alarms and Scaling

Planned alarm functions:

```text
Set Lower Alarm Limit
Set Upper Alarm Limit
Enable Lower Alarm
Enable Upper Alarm
Get Alarm Limits
Clear Alarm
Get Alarm State
```

Planned scaling functions:

```text
Set Scaling Gain
Set Scaling Offset
Set Scaling Unit
Enable Scaling
Disable Scaling
```

Planned digital-pattern functions:

```text
Configure Digital Pattern Alarm
Configure Digital Pattern Mask
```

All documented state changes caused by alarm configuration shall be recorded in the AI contract and protocol vectors.

---

## 18. 34972A-Specific Functions

34972A-only functionality shall be exposed only when the connected model supports it.

Potential capability families include:

```text
LAN configuration/query
LAN status
Hostname
DHCP
IP address
Gateway
Subnet mask

USB drive catalog
Configuration file import
Scan logging to USB
Memory/file operations
```

Calling a model-specific function on an unsupported mainframe shall raise a normalized `DriverUnsupportedOperationError`.

---

## 19. Calibration and Destructive Diagnostic Commands

Calibration and service-level commands shall not automatically become public Robot Framework keywords.

Default disposition:

```text
Calibration write commands:        EXCLUDED
Calibration security changes:      EXCLUDED
Relay-cycle counter reset:         EXCLUDED
Engineering DIAG POKE operations:  EXCLUDED
```

Read-only diagnostic operations may be exposed where safe and justified.

Every excluded vendor command shall remain visible in the vendor command coverage inventory.

---

## 20. Vendor Command Coverage Audit

Create:

```text
protocol/vendor_command_coverage.yaml
```

Every relevant command from the supplied device command reference shall receive an explicit disposition.

Example:

```yaml
- command: "SOURce:VOLTage"
  status: PUBLIC
  keyword: "Set DAC Voltage"

- command: "CALibration?"
  status: EXCLUDED
  reason: "Calibration/service operation requires separate service procedure."

- command: "DIAGnostic:POKE:SLOT:DATA"
  status: EXCLUDED
  reason: "Engineering/service operation not suitable for general automation."

- command: "<unverified-command>"
  status: UNKNOWN
  reason: "Authoritative behavior not established."
```

Allowed statuses:

```text
PUBLIC
PRIVATE
INTERNAL
EXCLUDED
NOT_APPLICABLE
UNKNOWN
DEPRECATED
```

This file shall prove that the vendor command source was reviewed systematically.

---

## 21. Safety Model

Safe shutdown shall be ownership-aware.

Example configuration:

```yaml
safety:
  abort_active_scan: true

  switching:
    owned_channels:
      - 201
      - 202
    safe_state:
      201: OPEN
      202: OPEN

  digital_outputs:
    owned_ports:
      - 301
    safe_values:
      301: 0

  dac_outputs:
    owned_channels:
      - 304
      - 305
    safe_voltage_v:
      304: 0.0
      305: 0.0
```

### 21.1 Safety rules

The driver shall:

- never blindly open or close every relay;
- never blindly zero every DAC;
- never assume exclusive ownership of shared bench resources;
- avoid replaying uncertain state-changing writes;
- log safety actions;
- use RFDS-018 bench data for deployment-specific safe states;
- fail closed when required safety information is unknown.

---

## 22. Retry and Recovery Rules

### 22.1 Read/query operations

Bounded retry may be allowed for operations that are demonstrably safe and idempotent.

Examples may include:

```text
*IDN?
SYST:ERR?
selected read-only status queries
```

### 22.2 State-changing operations

Automatic blind retry shall not be used where delivery may have occurred.

Examples:

```text
ROUT:CLOS ...
SOUR:VOLT ...
digital output writes
memory writes
configuration-changing commands
```

For uncertain delivery, recovery shall use an explicit reconciliation strategy such as:

```text
query state
compare expected state
recover or fail explicitly
```

---

## 23. Driver Configuration Model

The package shall implement all mandatory RFDS configuration keywords:

```text
Get Driver Configuration Schema
Get Driver Default Configuration
Get Driver Configuration
Validate Driver Configuration
Import Driver Configuration
Export Driver Configuration
Save Driver Configuration
Load Driver Configuration
List Driver Configuration Profiles
Delete Driver Configuration Profile
Reset Driver Configuration
```

Configuration layout:

```text
config/
├── schema.json
├── schema.lock
├── default.json
└── examples/
    ├── simulator.json
    ├── 34970a_gpib.json
    ├── 34970a_rs232.json
    └── 34972a_lan.json
```

### 23.1 Configuration requirements

Defaults shall:

- remain disconnected;
- contain no private IP addresses;
- contain no personal COM ports;
- contain no credentials;
- contain no bench-specific serial numbers;
- validate before application;
- never silently fall back from an explicitly requested invalid profile.

---

## 24. Plugin Architecture

Add:

```text
plugin.py
plugin_manifest.json
```

Expected plugin operations:

```python
get_descriptor()
validate_environment()
create_library()
discover_hardware()
```

Requirements:

- importing the plugin performs no hardware I/O;
- descriptor retrieval performs no hardware I/O;
- `create_library()` returns an unconnected driver;
- discovery is explicit and bounded;
- simulation shall never silently replace requested hardware.

The package shall expose the required RFDS plugin entry point through `pyproject.toml`.

---

## 25. AI Driver Contract

Create before implementation:

```text
ai/ai_contract.yaml
ai/ai_contract.lock
```

Each exported Robot Framework keyword shall include:

```text
canonical keyword
aliases
signature
purpose
inputs
input types
units
return schema
preconditions
postconditions
side effects
state transition
risk level
idempotency
timing
timeout
stabilization
retry policy
errors
resource ownership
verification oracle
supported models
supported modules
protocol operation
```

The contract shall explicitly model:

```text
34970A vs 34972A
installed module map
internal DMM installed/enabled
scan state
digital I/O direction
owned routing resources
34907A DAC state
transport type
```

The AI contract, capability model, public API inventory, and RFDS-019 protocol vectors shall remain synchronized.

---

## 26. RFDS-018 Test Bench Contract

The package shall provide a template:

```text
bench/system_ai_contract.template.yaml
```

A deployment-specific bench contract may define:

```text
device serial
transport resource
installed modules
wiring
DUT connections
switch ownership
safe relay states
digital output ownership
DAC restrictions
fixture requirements
operator actions
startup sequence
shutdown sequence
emergency behavior
```

The driver package shall not invent laboratory wiring or bench safety assumptions.

---

## 27. Stateful Protocol Simulator

A protocol-boundary simulator shall be implemented.

The simulator shall emulate at least:

```text
34970A identity
34972A identity
installed cards
internal DMM state
measurement configuration
scan list
routing state
trigger source
trigger count
trigger timer
reading memory
statistics
error queue
34907A digital I/O
34907A totalizer
34907A DAC
alarms
scaling
34972A-only capability behavior
```

### 27.1 Fault injection

The simulator shall support deterministic faults:

```text
timeout
delayed response
empty response
malformed response
malformed error queue response
unsupported command
device error
disconnect mid-query
partial read
reconnect
protocol recovery test
```

Simulator evidence shall always be labeled as simulator evidence.

Simulator results shall not be used to claim physical accuracy, real transport timing, or hardware safety validation.

---

## 28. RFDS-019 Protocol Conformance

Required tree:

```text
tests/conformance/
├── driver_call_protocol_conformance.robot
├── resources/
│   ├── conformance_keywords.resource
│   └── conformance_variables.resource
├── data/
│   ├── keyword_inventory.yaml
│   ├── protocol_vectors.yaml
│   └── exclusions.yaml
└── expected/
    └── response_schemas/
```

### 28.1 Required conformance coverage

For every exported public Robot Framework keyword:

```text
inventory status
canonical name
aliases
arguments/defaults
callability
device-facing classification
protocol vector
actual outbound protocol
raw inbound response
parsed return value
protocol error vectors
recovery vector
evidence reference
```

### 28.2 Acceptance target

The conformance suite shall provide:

- 100% public keyword inventory;
- 100% supported keyword callability;
- 100% device-facing keyword protocol-vector coverage or approved exclusion;
- outbound protocol verification;
- inbound protocol verification where applicable;
- return-value verification;
- error-vector verification;
- recovery verification;
- traceable evidence.

Trace capture shall begin before initial connection and identity traffic so that connection-time protocol operations are not omitted from evidence.

---

## 29. Testing Strategy

The completed project shall contain:

```text
tests/
├── unit/
├── protocol/
├── transport/
├── integration/
├── simulator/
├── robot/
├── conformance/
├── replay/
├── regression/
├── compatibility/
├── hil/
├── performance/
└── soak/
```

### 29.1 Mandatory verification sequence

1. Python compilation checks
2. Ruff
3. Type checking
4. Unit tests
5. Protocol serialization tests
6. Protocol parsing tests
7. Transport contract tests
8. Simulator tests
9. Python integration tests
10. Robot Framework acceptance tests
11. RFDS-019 conformance
12. Timeout tests
13. Malformed-response tests
14. Device-error tests
15. Recovery tests
16. Clean-wheel installation test
17. Real 34970A HIL
18. Real 34972A HIL when claimed supported
19. Card-specific HIL
20. Resource-locking tests
21. Performance tests
22. Soak/stability tests

---

## 30. Hardware-in-the-Loop Matrix

Qualification shall be recorded by mainframe, transport, and module.

### 30.1 Mainframes

```text
34970A
34972A
```

### 30.2 Transports

```text
34970A GPIB
34970A RS-232
34972A LAN / VISA
34972A USB / VISA
```

### 30.3 Modules

```text
34901A
34902A
34903A
34904A
34905A
34906A
34907A
34908A
```

Each combination shall carry an explicit status:

```text
NOT_TESTED
SIMULATOR_TESTED
HARDWARE_TESTED
EXCLUDED
NOT_APPLICABLE
```

No unsupported HIL combination shall be silently represented as validated.

---

## 31. Examples

At least ten runnable examples are required.

Planned examples:

```text
01_identity_and_modules.robot
02_dc_voltage_measurement.robot
03_resistance_2wire.robot
04_resistance_4wire.robot
05_temperature_thermocouple.robot
06_temperature_rtd.robot
07_scan_multiple_channels.robot
08_triggered_scan.robot
09_buffered_readings.robot
10_statistics.robot
11_switch_control.robot
12_34907a_digital_io.robot
13_34907a_totalizer.robot
14_34907a_dac.robot
15_configuration_and_diagnostics.robot
```

Every example shall support a simulator profile.

Hardware examples shall require explicit connection configuration.

No example shall contain hard-coded personal addresses, IPs, COM ports, or credentials.

---

## 32. Scripts

The package shall include scripts for Windows and Linux where practical.

Planned scripts:

```text
scripts/
├── setup_env.ps1
├── setup_env.sh
├── run_unit_tests.ps1
├── run_unit_tests.sh
├── run_examples.ps1
├── run_examples.sh
├── run_conformance.ps1
├── run_conformance.sh
├── build_docs.ps1
├── build_docs.sh
├── build_dist.ps1
├── build_dist.sh
├── validate_package.ps1
├── validate_package.sh
├── release_check.ps1
└── release_check.sh
```

---

## 33. Documentation

The package shall include current documentation for every release.

### 33.1 README

`README.md` shall include:

- supported instruments;
- supported modules;
- installation;
- quick start;
- connection examples;
- simulator usage;
- Robot Framework usage;
- limitations;
- safety notes;
- conformance status;
- HIL status;
- links to detailed documentation.

### 33.2 GitHub Pages

GitHub Pages shall be updated for every driver revision.

Planned documentation:

```text
docs/
├── index.md
├── architecture.md
├── installation.md
├── configuration.md
├── keywords.md
├── modules.md
├── measurements.md
├── scanning.md
├── switching.md
├── 34907a.md
├── safety.md
├── simulator.md
├── call_protocol_conformance.md
├── hardware_validation.md
├── troubleshooting.md
└── release_notes.md
```

---

## 34. PyCharm and Robot Framework Guide

Required guide folder:

```text
guide/
├── pycharm_robot_framework_setup.md
├── windows_setup.md
├── linux_setup.md
├── hardware_setup.md
├── configuration_profiles.md
└── troubleshooting.md
```

The PyCharm guide shall include:

- Python interpreter setup;
- virtual environment creation;
- package installation;
- Robot Framework installation;
- Robot Framework language support;
- library import configuration;
- project source root;
- running Robot tests;
- debugging Python driver code;
- selecting simulator profiles;
- selecting real hardware profiles.

---

## 35. History Folder

Required:

```text
history/
```

Each meaningful driver change shall have a traceable history record.

Recommended naming:

```text
history/
├── v26.01.00-g1.md
├── v26.01.00-g2.md
├── v26.01.00-g3.md
├── v26.01.00-g4.md
├── v26.01.00-g5.md
└── v26.01.00.md
```

Each history record shall include:

```text
date
version
gate
changed requirements
changed files
new capabilities
changed capabilities
bug fixes
known limitations
tests executed
evidence references
```

---

## 36. Review Folder

Required:

```text
review/
```

Each major gate shall have a code/release review.

Recommended files:

```text
review/
├── g1_architecture_review.md
├── g2_code_review.md
├── g3_feature_review.md
├── g4_test_documentation_review.md
├── g5_release_review.md
├── safety_review.md
├── security_review.md
├── api_review.md
└── production_readiness_review.md
```

Review shall use RFDS-010 as the minimum checklist.

---

## 37. Planned Package Structure

```text
rf_keysight349xx/
├── README.md
├── CHANGELOG.md
├── LICENSE
├── SECURITY.md
├── CONTRIBUTING.md
├── AGENTS.md
├── pyproject.toml
├── mkdocs.yml
│
├── src/
│   └── rf_keysight349xx/
│       ├── __init__.py
│       ├── library.py
│       ├── version.py
│       ├── plugin.py
│       ├── sessions.py
│       ├── converters.py
│       ├── capabilities.py
│       ├── configuration.py
│       ├── diagnostics.py
│       │
│       ├── core/
│       │   ├── instrument.py
│       │   ├── measurement.py
│       │   ├── scanner.py
│       │   ├── switching.py
│       │   ├── temperature.py
│       │   ├── digital_io.py
│       │   ├── totalizer.py
│       │   ├── dac.py
│       │   ├── alarms.py
│       │   └── scaling.py
│       │
│       ├── protocol/
│       │   ├── scpi.py
│       │   ├── parsers.py
│       │   ├── commands.py
│       │   └── vendor_command_coverage.yaml
│       │
│       └── transports/
│           ├── factory.py
│           └── simulator.py
│
├── api/
│   ├── public_api.yaml
│   ├── unknowns.yaml
│   └── deviations.yaml
│
├── capabilities/
│   └── capabilities.yaml
│
├── config/
│   ├── schema.json
│   ├── schema.lock
│   ├── default.json
│   └── examples/
│
├── ai/
│   ├── ai_contract.yaml
│   └── ai_contract.lock
│
├── bench/
│   └── system_ai_contract.template.yaml
│
├── tests/
│   ├── unit/
│   ├── protocol/
│   ├── transport/
│   ├── integration/
│   ├── robot/
│   ├── simulator/
│   ├── replay/
│   ├── conformance/
│   ├── regression/
│   ├── compatibility/
│   ├── hil/
│   ├── performance/
│   └── soak/
│
├── examples/
│   ├── index.yaml
│   ├── README.md
│   └── *.robot
│
├── scripts/
│   ├── *.ps1
│   └── *.sh
│
├── guide/
│   └── *.md
│
├── docs/
│   └── *.md
│
├── history/
├── review/
│
├── dist/
│
└── release/
    ├── release_manifest.yaml
    ├── decisions.yaml
    ├── open_questions.yaml
    ├── requirements_traceability.csv
    ├── compatibility_report.json
    ├── validation_report.json
    ├── sbom.spdx.json
    └── checksums.sha256
```

---

## 38. Implementation Lifecycle

The project shall use 12 implementation phases.

Each phase contains five gates:

```text
Gate 1 — Architecture & Skeleton
Gate 2 — Core Implementation
Gate 3 — Extended Features
Gate 4 — Tests & Documentation
Gate 5 — Review & Release
```

---

## 39. Phase 1 — Requirements, Contracts, Architecture, Skeleton

### Gate 1

- Freeze authoritative source set.
- Create requirement traceability matrix.
- Create package skeleton.
- Define driver identity.
- Define public API inventory.
- Define initial capability inventory.
- Define AI contract skeleton.
- Define protocol vector schema.
- Define vendor command coverage inventory.
- Record all unresolved behavior as `UNKNOWN`.

### Gate 2

- Implement base library structure.
- Integrate BaseInstrumentLibrary.
- Implement RFDS transport interfaces.
- Implement simulator transport skeleton.
- Implement normalized exceptions.
- Implement timeout framework.
- Implement session state model.

### Gate 3

- Add transport observation hooks.
- Add configuration schema framework.
- Add capability model framework.
- Add plugin provider skeleton.
- Add ownership model.
- Add logging/evidence infrastructure.

### Gate 4

- Unit-test base state machine.
- Test zero-I/O import/construction.
- Test timeout behavior.
- Test partial-connect cleanup.
- Create initial documentation.
- Create initial PyCharm setup guide.

### Gate 5

- Architecture review.
- API review.
- safety model review.
- RFDS requirement review.
- Generate Gate-1 phase package.

---

## 40. Phase 2 — Connection, Identity, Modules, System, Errors

### Gate 1

- Define protocol vectors for connection.
- Define identity parser.
- Define module discovery behavior.
- Define system/error API.

### Gate 2

- Implement connect/disconnect.
- Implement `*IDN?`.
- Implement module discovery.
- Implement communication probe.
- Implement SCPI version.
- Implement error queue.

### Gate 3

- Add 34970A/34972A model branching.
- Add connection-error recovery.
- Add malformed `SYST:ERR?` handling.
- Add self-test and status behavior.

### Gate 4

- Robot tests.
- simulator tests.
- RFDS-019 vectors.
- documentation.
- examples.

### Gate 5

- Code review.
- protocol review.
- conformance review.
- package review.
- gate ZIP.

---

## 41. Phase 3 — Measurement Engine

Implement:

- DC voltage;
- AC voltage;
- DC current;
- AC current;
- 2-wire resistance;
- 4-wire resistance;
- frequency;
- period;
- applicable measurement configuration.

Each measurement keyword shall receive:

- public API definition;
- AI contract entry;
- protocol vector;
- unit test;
- simulator behavior;
- Robot test;
- documentation;
- example;
- RFDS-019 evidence.

---

## 42. Phase 4 — Scan, Trigger, Acquisition, Memory, Statistics

Implement:

- scan list;
- trigger source;
- trigger count;
- trigger timer;
- initiate;
- abort;
- read;
- fetch;
- buffered read;
- reading count;
- reading memory;
- statistics;
- min/max timestamps.

Special attention shall be given to differing memory semantics of `READ?`, `FETCh?`, `R?`, and `DATA:REMove?`.

---

## 43. Phase 5 — Temperature

Implement:

- thermocouple;
- RTD;
- thermistor;
- temperature units;
- four-wire pairing;
- module restrictions;
- sensor-specific configuration.

The simulator shall reproduce valid and invalid sensor/module combinations.

---

## 44. Phase 6 — Switching and Routing

Implement:

- channel enumeration;
- open;
- close;
- multi-channel operations;
- switch-state query;
- ownership;
- safe-state behavior.

Switching commands shall use conservative retry semantics.

---

## 45. Phase 7 — 34907A Digital I/O, Totalizer, DAC

Implement:

- digital byte/word input;
- digital byte/word output;
- direction state;
- totalizer;
- DAC output;
- DAC readback;
- ownership;
- safety;
- fault recovery.

This phase requires explicit high-risk protocol vectors for state-changing functions.

---

## 46. Phase 8 — Alarms, Scaling, Status, Diagnostics

Implement:

- alarm limits;
- alarm enable/disable;
- alarm state;
- digital compare/mask;
- scaling;
- supported status queries;
- safe diagnostics.

Service-only operations remain excluded.

---

## 47. Phase 9 — 34972A-Specific Functions

Implement only functions established by authoritative 34972A documentation.

Expected areas:

- LAN configuration/status;
- hostname;
- DHCP;
- network parameters;
- USB storage catalog;
- file/memory operations;
- logging.

Model gating shall be mandatory.

---

## 48. Phase 10 — Configuration, Safety, Recovery, Plugin, AI/GUI Integration

Complete:

- RFDS-014 configuration API;
- configuration profiles;
- safe shutdown;
- ownership reconciliation;
- retry policy;
- session recovery;
- plugin architecture;
- final AI contract;
- capability model;
- GUI integration metadata.

---

## 49. Phase 11 — Full Verification and Documentation

Complete:

- RFDS-019;
- regression suite;
- compatibility suite;
- replay tests;
- clean-wheel test;
- simulator qualification;
- real HIL;
- module HIL;
- examples;
- README;
- GitHub Pages;
- guide;
- traceability;
- review evidence.

---

## 50. Phase 12 — Production Qualification

Complete:

- performance;
- concurrency;
- soak;
- stability;
- security review;
- safety review;
- package review;
- SBOM;
- checksums;
- release manifest;
- final production-readiness review.

No production claim shall be made while mandatory acceptance evidence remains `NOT_RUN`.

---

## 51. Release Maturity Progression

Recommended progression:

```text
D0
architecture / incomplete development
     ↓
D1
complete simulator + RFDS-019 validation
     ↓
D2
representative real hardware validated
     ↓
P1
full production acceptance
```

The first substantial target should be:

```text
rf_keysight349xx_v26.01.00 — D1
```

Promotion beyond D1 requires real hardware evidence.

---

## 52. Requirement Traceability

Create:

```text
release/requirements_traceability.csv
```

Recommended fields:

```text
requirement_id
source_document
source_section
requirement_summary
implementation_artifact
test_artifact
evidence_artifact
status
deviation_id
notes
```

Allowed status values:

```text
PASS
IMPLEMENTED
NOT_APPLICABLE
UNKNOWN
EXCLUDED
DEVIATION
FAIL
NOT_RUN
```

No mandatory requirement shall disappear from traceability.

---

## 53. Definition of Done

The driver is ready for production review only when all of the following are true:

- package structure conforms to RFDS;
- all mandatory universal keywords exist;
- applicable conditional keyword groups are complete;
- all exported keywords are in RFDS-019 inventory;
- every device-facing keyword has a protocol vector or approved exclusion;
- protocol transmission is verified;
- response parsing is verified;
- malformed responses are tested;
- timeout behavior is tested;
- recovery behavior is tested;
- configuration API is complete;
- AI contract is synchronized;
- capability model is synchronized;
- safe shutdown is ownership-aware;
- simulator suite passes;
- real-device evidence exists for claimed hardware support;
- examples are runnable;
- at least ten examples exist;
- README is current;
- GitHub Pages are current;
- setup guides are current;
- history is current;
- code reviews are present;
- release manifest is generated;
- SBOM is generated;
- checksums are generated;
- clean installation test passes;
- no mandatory release criterion remains `NOT_RUN`.

---

## 54. Initial Open Questions

The following items shall remain explicit until resolved by authoritative source or hardware verification:

1. Exact final public keyword naming for every device-specific function.
2. Exact capability support matrix for every mainframe/card combination.
3. Whether continuity measurement is supported.
4. Whether diode measurement is supported.
5. Which calibration/service queries, if any, should be read-only public diagnostics.
6. Exact safe states for deployment-specific relay, digital-output, and DAC resources.
7. Which 34972A memory and USB operations should become public keywords.
8. Which real hardware combinations are available for HIL.
9. Which firmware revisions require compatibility exceptions.
10. Whether any module-specific timing restrictions require additional stabilization parameters.

These questions shall not be silently resolved by assumptions.

---

## 55. Implementation Principle

The driver shall be built source-first and evidence-first:

```text
RFDS requirement
      ↓
device source
      ↓
public capability
      ↓
AI contract
      ↓
protocol vector
      ↓
implementation
      ↓
simulator / unit test
      ↓
Robot Framework test
      ↓
RFDS-019 evidence
      ↓
real hardware evidence
      ↓
release review
```

This traceability chain is the central iacceptance model for the project.
1. 