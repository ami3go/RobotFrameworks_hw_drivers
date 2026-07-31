# RFDS-013 — Driver Capability Model and Feature Discovery Specification

**Version:** 1.0  
**Document ID:** RFDS-013  
**Status:** Draft project requirement  
**Applies to:** All RFDS Robot Framework driver packages  
**Primary audience:** Driver developers, generic application developers, test planners, GUI/CLI developers, orchestration systems, and AI agents

---

## 1. Purpose

This specification defines the mandatory, machine-readable **capability model** that allows a generic application to discover what an RFDS driver can do without importing driver source code, hard-coding device-specific keyword names, or interpreting free-form documentation.

The model shall allow a generic application to determine:

1. driver identity and version;
2. supported functional capabilities;
3. public Robot Framework keywords that implement each capability;
4. required and optional arguments;
5. argument types, ranges, units, enumerations, and defaults;
6. returned values and result schemas;
7. required connection and driver states;
8. capability availability in the current runtime state;
9. side effects, timing, risk, and resource use;
10. supported channels, modes, features, and limits;
11. safe setup, execution, and cleanup operations;
12. capability dependencies and conflicts;
13. deprecation, aliases, and compatibility information;
14. how to invoke the capability through Robot Framework;
15. whether capability information is static, configured, detected, or queried from the device.

The intended discovery path is:

```text
Generic application
        ↓
RFDS capability discovery interface
        ↓
machine-readable driver capability model
        ↓
selected capability and invocation binding
        ↓
public Robot Framework keyword
        ↓
driver and physical device
```

The capability model is a **functional discovery contract**. It is not merely generated keyword documentation.

---

## 2. Goals

RFDS-013 shall enable the following classes of generic application:

- device setup applications;
- instrument control panels;
- test-sequence editors;
- Robot Framework test generators;
- automatic bench planners;
- test-execution dashboards;
- remote-control services;
- capability browsers;
- driver compatibility checkers;
- multi-instrument orchestration systems;
- AI-assisted test-development tools.

A conforming application shall be able to discover and use common driver functions without a device-specific software plug-in when those functions are represented by the standard capability taxonomy defined in this specification.

---

## 3. Scope Boundary

### 3.1 In scope

RFDS-013 covers:

- a canonical capability taxonomy;
- stable capability identifiers;
- capability metadata and schemas;
- mapping capabilities to public Robot Framework keywords;
- discovery of supported functionality;
- static and runtime capability information;
- state-aware availability;
- device-derived limits and supported options;
- channel and subsystem discovery;
- argument and return-value metadata;
- units, numeric constraints, and enumerations;
- preconditions, postconditions, and side effects;
- resource ownership and conflicts;
- risk and safety metadata;
- timing and stabilization metadata;
- feature dependencies;
- aliases and deprecation;
- model validation and compatibility;
- discovery through Python and Robot Framework;
- cached and live discovery modes;
- evidence required to prove model accuracy.

### 3.2 Out of scope

RFDS-013 does not define:

- the complete mandatory public driver API;
- the internal Python architecture of a driver;
- transport implementation details;
- complete device protocol mappings;
- full vendor-manual feature coverage;
- physical measurement accuracy;
- calibration procedures;
- test-bench wiring;
- complete AI planning semantics;
- implementation lifecycle and release gates;
- package structure beyond the RFDS-013 artifacts;
- graphical layout of a generic application;
- protocol conformance testing;
- security authentication protocols.

These matters are addressed by other RFDS specifications and device-specific requirements.

---

## 4. Normative Terminology

- **shall / shall not** — mandatory requirement;
- **should / should not** — recommended requirement; deviations require justification;
- **may** — permitted implementation choice;
- **capability** — a normalized function the driver can perform;
- **feature** — a supported option, mode, subsystem, or device characteristic;
- **capability binding** — the mapping from a capability to a public Robot Framework keyword;
- **static discovery** — capability information available without opening the device;
- **configured discovery** — capability information derived from driver configuration;
- **live discovery** — capability information obtained from the connected device;
- **effective capability model** — the merged result of static, configured, and live discovery;
- **availability** — whether a capability can be invoked in the current state;
- **support state** — whether a capability is implemented, unavailable, restricted, or unknown.

---

## 5. Design Principles

### 5.1 Stable semantics

Capability meaning shall be represented by a stable identifier rather than inferred only from a human-readable Robot Framework keyword name.

### 5.2 Keyword independence

A generic application shall identify the intended function by `capability_id`. The model shall separately provide the public keyword used to invoke it.

### 5.3 Explicit constraints

A generic application shall not be required to parse prose to determine valid ranges, units, enumerations, required states, or return types.

### 5.4 State awareness

The model shall distinguish between:

- implemented capability;
- capability available in the current connection and device state;
- capability temporarily blocked by another operation;
- capability unsupported by the detected model or installed module;
- capability whose support cannot be determined.

### 5.5 Safe generic use

Capabilities that can energize outputs, move mechanisms, modify calibration, erase data, reset hardware, change firmware, or otherwise create risk shall expose explicit risk and confirmation metadata.

### 5.6 Conservative discovery

The driver shall not report a capability as supported unless the implementation can invoke it through the declared public interface.

### 5.7 Deterministic output

For the same driver version, configuration, device identity, installed modules, and device state, discovery output shall be semantically deterministic.

### 5.8 Extensibility

Vendor-specific capabilities may be added without changing the meaning of standard RFDS capability identifiers.

---

## 6. Required Artifacts

Each driver package shall provide:

```text
rf_<driver_name>/
├── capability/
│   ├── capability_model.yaml
│   ├── capability_model.schema.json
│   ├── capability_taxonomy_extensions.yaml      # optional
│   └── examples/
│       ├── capability_snapshot.json
│       └── capability_query_examples.robot
├── tests/
│   └── capability/
│       ├── capability_model_validation.robot
│       ├── capability_binding_validation.robot
│       ├── capability_runtime_discovery.robot
│       └── expected/
│           └── minimum_capabilities.yaml
└── docs/
    └── capability_model.md
```

Equivalent locations may be used only when the package specification explicitly defines them and all references remain deterministic.

The release package shall contain a validated static capability model even when live device discovery is also supported.

---

## 7. Discovery Interfaces

### 7.1 Mandatory Robot Framework keywords

Every RFDS driver shall expose the following public discovery keywords or project-standard aliases defined by RFDS-002:

```robotframework
Get Capability Model
Get Driver Capability
Find Driver Capabilities
Get Driver Features
Refresh Driver Capabilities
Validate Driver Capabilities
```

`Get Capability Model` is deliberately distinct from RFDS-002's `Get Driver Capabilities`, which returns the fixed, flat `list[str]` of RFDS-002 group-level capability names. `Get Capability Model` returns the richer RFDS-013 structure defined below. A driver shall implement both, and the AI Driver Contract shall map each RFDS-002 group name to its corresponding RFDS-013 `capability_id` entries.

The canonical behavior shall be:

| Keyword | Required behavior |
|---|---|
| `Get Capability Model` | Return the effective capability model or a filtered capability list. |
| `Get Driver Capability` | Return one capability by exact capability ID. |
| `Find Driver Capabilities` | Return capabilities matching structured filters. |
| `Get Driver Features` | Return normalized device and driver feature data. |
| `Refresh Driver Capabilities` | Re-evaluate configured and live capability information. |
| `Validate Driver Capabilities` | Validate the model and bindings; return a structured validation result. |

A driver may expose additional convenience discovery keywords, but they shall not replace the canonical discovery behavior.

### 7.2 Mandatory Python interface

The driver shall expose equivalent Python-callable operations:

```python
get_capability_model(...)
get_driver_capability(capability_id, ...)
find_driver_capabilities(...)
get_driver_features(...)
refresh_driver_capabilities(...)
validate_driver_capabilities(...)
```

The exact class layout is implementation-defined, but the public behavior and returned schemas shall conform to this specification.

### 7.3 Return transport

The discovery keywords shall return Robot Framework-compatible values composed only of:

- dictionaries;
- lists;
- strings;
- integers;
- finite floating-point values;
- booleans;
- `None` where explicitly allowed.

The default return shall not require consumers to instantiate driver-specific Python classes.

### 7.4 Serialization

The model shall be serializable to JSON without loss of semantic information.

YAML may be used as the maintained source file. Runtime discovery results shall be exportable as JSON.

---

## 8. Discovery Modes

Every discovery response shall identify its discovery mode.

### 8.1 Static mode

Static mode shall be available without opening the transport or communicating with the device.

It shall describe:

- capabilities implemented by the installed driver;
- public keyword bindings;
- generic argument and result structure;
- driver-declared limits that do not depend on connected hardware;
- known supported model families;
- capability metadata that is valid before connection.

### 8.2 Configured mode

Configured mode may refine the model using:

- selected transport;
- configured model profile;
- enabled modules;
- feature flags;
- driver configuration file;
- simulator profile;
- user-selected channel count;
- optional dependency availability.

### 8.3 Live mode

Live mode may communicate with the device to determine:

- detected manufacturer and model;
- firmware version;
- installed modules;
- channel count;
- supported ranges;
- available modes;
- option codes;
- protocol feature support;
- current operating state;
- lock or interlock state;
- device-derived constraints.

Live discovery shall not make hazardous state changes solely to determine support.

### 8.4 Effective mode

The effective model shall merge static, configured, and live data according to the precedence rules in Section 22.

---

## 9. Top-Level Capability Model

The capability model shall contain at least:

```yaml
schema:
  name: rfds-capability-model
  version: "1.0"

driver:
  id: rf_keysight_n6700
  name: Keysight N6700 Robot Framework Driver
  version: "26.03"
  api_version: "1.0"
  capability_model_version: "1.0"

source:
  discovery_mode: effective
  generated_at: "2026-07-26T12:00:00+03:00"
  connected: true
  stale: false

identity:
  manufacturer: Keysight Technologies
  model: N6705C
  serial_number: MY00000000
  firmware_version: A.03.10

features: {}
resources: []
capabilities: []
validation: {}
extensions: {}
```

### 9.1 Mandatory top-level fields

| Field | Requirement |
|---|---|
| `schema` | Capability schema name and version. |
| `driver` | Driver identity and version information. |
| `source` | Discovery source, timestamp, connection state, and freshness. |
| `identity` | Known device identity; unknown fields shall be explicit. |
| `features` | Normalized device and driver feature information. |
| `resources` | Channels, subsystems, endpoints, or exclusive resources. |
| `capabilities` | Capability records. |
| `validation` | Model and binding validation summary. |
| `extensions` | Namespaced vendor or project extensions. |

---

## 10. Capability Taxonomy

### 10.1 Capability ID format

A standard capability ID shall use lowercase dot-separated segments:

```text
<domain>.<object>.<operation>
```

Examples:

```text
connection.session.open
connection.session.close
identity.device.read
source.voltage.set
source.voltage.read
source.output.enable
measure.voltage.dc
measure.resistance.two_wire
load.current.set
switch.relay.close
switch.relay.open
system.error.read
system.reset.execute
file.calibration.upload
```

IDs shall be stable across driver versions when the capability semantics remain compatible.

### 10.2 Standard domains

RFDS defines the following primary domains:

| Domain | Purpose |
|---|---|
| `connection` | Open, close, reconnect, detect, and transport-session functions. |
| `identity` | Device, driver, firmware, module, and option identification. |
| `configuration` | Non-measurement configuration and operating modes. |
| `source` | Generate or apply electrical, digital, thermal, mechanical, or other stimuli. |
| `measure` | Acquire measured values. |
| `load` | Apply an electrical or mechanical load. |
| `switch` | Relays, matrices, routing, and connection states. |
| `trigger` | Trigger setup, arming, initiation, and status. |
| `acquisition` | Sampling, capture, buffering, and trace acquisition. |
| `waveform` | Waveform definition, generation, and retrieval. |
| `channel` | Channel selection, configuration, and metadata. |
| `status` | Operational, condition, event, and readiness status. |
| `system` | Reset, self-test, error queue, time, health, and general system functions. |
| `safety` | Output inhibition, interlocks, limits, and emergency actions. |
| `calibration` | Calibration data and calibration workflows. |
| `file` | Device file and data transfer operations. |
| `logging` | Driver or device logging and diagnostic capture. |
| `firmware` | Firmware identity, update, and rollback operations. |
| `simulation` | Simulator controls and simulation-state discovery. |
| `utility` | Generic conversion or helper operations with no better domain. |

### 10.3 Standard operation verbs

The final segment should use a normalized verb where applicable:

```text
open, close, connect, disconnect, reconnect, detect,
read, query, get, set, configure, enable, disable,
start, stop, initiate, abort, clear, reset, execute,
upload, download, list, delete, validate, refresh,
measure, acquire, route, select, wait, check
```

`get` shall normally represent driver-held or cached information.  
`read` or `query` shall normally represent an operation that communicates with the device.  
`measure` shall represent a measurement operation with measurement semantics.

### 10.4 Vendor-specific IDs

Vendor-specific capabilities shall be namespaced:

```text
vendor.<vendor_id>.<domain>.<object>.<operation>
```

Example:

```text
vendor.keysight.n6700.smu.quadrant.configure
```

A vendor-specific capability shall not redefine a standard RFDS capability ID with incompatible semantics.

---

## 11. Capability Record

Each capability record shall contain at least:

```yaml
capability_id: source.voltage.set
display_name: Set DC Voltage
description: Set the programmed DC output voltage for one channel.
category: source
standard: true
support:
  state: supported
  reason: null
  confidence: confirmed
binding:
  robot_keyword: Set DC Voltage
  canonical_keyword: Set DC Voltage
  aliases: []
  python_method: set_dc_voltage
  library: rf_keysight_n6700.KeysightN6700Library
arguments: []
returns: []
preconditions: []
postconditions: []
side_effects: []
availability: {}
timing: {}
risk: {}
resources: []
dependencies: []
conflicts: []
cleanup: []
provenance: {}
lifecycle: {}
```

### 11.1 Identity fields

Each capability shall define:

- `capability_id`;
- `display_name`;
- `description`;
- `category`;
- `standard`.

### 11.2 Support fields

Each capability shall define:

- `support.state`;
- `support.reason`;
- `support.confidence`;
- `support.detected_for` when support is model-specific;
- `support.requires_option` when an optional module or licence is required.

### 11.3 Binding fields

Each executable capability shall define:

- public Robot Framework keyword;
- canonical keyword name;
- aliases;
- Python method or adapter target;
- importable library name;
- whether the binding is direct, adapter-based, composed, or virtual.

A capability may be descriptive-only only when `binding.executable` is `false` and the reason is explicit.

---

## 12. Support States

Only the following support states are permitted:

| State | Meaning |
|---|---|
| `supported` | Implemented and supported for the effective device/profile. |
| `unsupported` | Not supported by the driver or effective device/profile. |
| `conditional` | Supported only when declared conditions are satisfied. |
| `restricted` | Implemented but intentionally restricted by safety, role, policy, or profile. |
| `unavailable` | Supported in principle but currently unavailable because of runtime state or missing prerequisite. |
| `deprecated` | Supported for compatibility but scheduled for removal. |
| `unknown` | Support cannot be determined safely or reliably. |

`unknown` shall not be interpreted as `supported`.

---

## 13. Support Confidence

The `support.confidence` field shall use:

- `declared` — based on the static driver model;
- `configured` — based on selected configuration;
- `detected` — inferred from connected-device information;
- `confirmed` — verified by a safe device query or capability test;
- `assumed` — temporarily inferred; shall include justification;
- `unknown` — no reliable determination.

A generic application may use confidence to choose whether operator confirmation is needed.

---

## 14. Argument Model

Each argument shall provide equivalent information to:

```yaml
- name: voltage
  display_name: Voltage
  position: 2
  required: true
  type: number
  python_type: float
  robot_type: float
  unit: V
  quantity: electric_potential
  minimum: 0.0
  maximum: 20.0
  minimum_inclusive: true
  maximum_inclusive: true
  resolution: 0.001
  default: null
  enum: null
  pattern: null
  allow_none: false
  semantic_role: setpoint
  channel_dependent: true
  source: live
  description: Programmed channel voltage.
```

### 14.1 Required argument fields

Every argument shall define:

- name;
- required/optional status;
- logical type;
- Robot Framework-compatible type;
- position or named-only behavior;
- default when optional;
- nullability;
- description.

### 14.2 Supported logical types

The following logical types are standard:

```text
string
integer
number
boolean
enum
list
object
binary
path
duration
timestamp
channel
resource_reference
capability_reference
```

### 14.3 Units and quantities

Numeric physical values shall declare:

- unit;
- physical quantity;
- minimum and maximum where known;
- inclusivity;
- resolution or step where known;
- tolerance where relevant;
- whether values are device-, range-, mode-, or channel-dependent.

SI unit symbols should be used where appropriate.

A missing unit shall mean dimensionless only when explicitly declared.

### 14.4 Enumerations

Enumerated arguments shall define stable machine values and human-readable labels:

```yaml
enum:
  - value: CC
    label: Constant Current
    aliases: [CURRENT]
  - value: CV
    label: Constant Voltage
    aliases: [VOLTAGE]
```

### 14.5 Dynamic constraints

When a constraint depends on another argument or feature, the model shall express the dependency:

```yaml
constraints:
  - when:
      argument: range
      equals: LOW
    maximum: 1.0
  - when:
      feature: module.model
      equals: N6775A
    maximum: 20.0
```

Free-form descriptions may supplement, but shall not replace, structured constraints.

### 14.6 Sensitive arguments

Credentials, tokens, and secrets shall be marked:

```yaml
sensitive: true
redact_in_logs: true
```

Discovery output shall not contain secret values.

---

## 15. Return Model

Each return value shall define:

- name;
- type;
- Robot Framework-compatible representation;
- unit and physical quantity when applicable;
- schema for objects or lists;
- nullability;
- meaning;
- whether the value is measured, programmed, cached, calculated, or device-reported;
- timestamp behavior when applicable;
- quality or validity indicators where applicable.

Example:

```yaml
returns:
  - name: measured_voltage
    type: number
    robot_type: float
    unit: V
    quantity: electric_potential
    value_origin: measured
    nullable: false
  - name: metadata
    type: object
    schema_ref: measurement_result_v1
    nullable: false
```

A structured measurement result should support:

```yaml
value: 4.9987
unit: V
timestamp: "2026-07-26T12:00:00.125+03:00"
channel: 1
status: valid
range: 10V
resolution: 0.0001
```

A driver may return a scalar for simple compatibility while also declaring an optional structured result capability.

---

## 16. Features Model

Features represent discoverable driver or device characteristics that are not themselves invocable operations.

Examples include:

- channel count;
- channel names;
- installed modules;
- supported measurement functions;
- supported source modes;
- ranges;
- maximum sample rate;
- trigger sources;
- transport types;
- simulator availability;
- binary block support;
- error queue support;
- remote/local mode support;
- firmware update support;
- hardware interlock presence.

Feature keys shall use lowercase dot-separated identifiers:

```yaml
features:
  channel.count:
    value: 4
    type: integer
    source: live
  transport.supported:
    value: [usb, tcpip, gpib]
    type: list
    source: static
  source.voltage.ranges:
    value: [5.0, 10.0, 20.0]
    unit: V
    type: list
    source: live
```

Each feature shall identify:

- value;
- type;
- source;
- confidence;
- freshness;
- scope;
- unknown reason when not known.

---

## 17. Resource Model

A resource is a logical or physical entity consumed, controlled, or observed by a capability.

Standard resource types include:

- driver instance;
- transport session;
- instrument;
- channel;
- output;
- input;
- relay;
- switch path;
- trigger bus;
- acquisition engine;
- file system;
- calibration store;
- firmware updater;
- fixture;
- operator;
- safety interlock.

Example:

```yaml
resources:
  - resource_id: channel.1
    type: channel
    display_name: Output Channel 1
    parent: instrument.main
    state: available
    attributes:
      module_model: N6775A
      four_quadrant: false
```

Capability records shall declare resource access:

```yaml
resources:
  - resource_id: channel.{channel}
    access: exclusive_write
  - resource_id: transport.session
    access: shared
```

Allowed access modes are:

- `read`;
- `shared`;
- `exclusive_write`;
- `exclusive_operation`;
- `consumes`;
- `provides`.

---

## 18. Preconditions, Postconditions, and State

### 18.1 Preconditions

A capability shall declare every required state that a generic application must establish before invocation.

Example:

```yaml
preconditions:
  - condition: driver.connected
    equals: true
    satisfaction_capability: connection.session.open
  - condition: channel.enabled
    equals: false
    reason: Range may only be changed with output disabled.
```

### 18.2 Postconditions

Capabilities that change state shall declare expected postconditions:

```yaml
postconditions:
  - condition: channel.voltage_setpoint
    equals_argument: voltage
```

### 18.3 State keys

State identifiers shall be stable and machine-readable, for example:

```text
driver.connected
driver.busy
device.remote
channel.<n>.enabled
channel.<n>.mode
acquisition.armed
calibration.active
firmware.update_active
safety.interlock_closed
```

### 18.4 State acquisition

The capability model shall identify how state is obtained:

- cached driver state;
- device query;
- calculated state;
- configured state;
- unknown.

A generic application shall not be told that a precondition is satisfied when the driver cannot determine it reliably.

---

## 19. Runtime Availability

Capability support and current availability are separate properties.

Each capability shall provide:

```yaml
availability:
  available: true
  state: ready
  reason: null
  checked_at: "2026-07-26T12:00:00+03:00"
  valid_for_s: 5
  blocking_resources: []
  missing_preconditions: []
```

Allowed availability states are:

- `ready`;
- `not_connected`;
- `busy`;
- `blocked`;
- `interlocked`;
- `missing_dependency`;
- `wrong_mode`;
- `wrong_device`;
- `restricted`;
- `stale`;
- `unknown`.

Availability checks shall not silently perform the operation being checked.

---

## 20. Side Effects and Cleanup

Each capability shall declare side effects, including:

- output state changes;
- signal generation;
- relay movement;
- device mode changes;
- data acquisition;
- buffer clearing;
- file creation or deletion;
- persistent configuration changes;
- calibration changes;
- reboot;
- transport reconnection;
- operator-visible effects.

Example:

```yaml
side_effects:
  - type: output_change
    target: channel.{channel}
    persistent_after_call: true

cleanup:
  required: true
  capabilities:
    - source.output.disable
  automatic_on_failure: recommended
```

A generic application shall be able to determine whether cleanup is required before it invokes a capability.

---

## 21. Timing and Execution Characteristics

Each executable capability shall declare:

```yaml
timing:
  timeout_s: 10
  typical_duration_s: 0.2
  maximum_duration_s: 5
  stabilization_s: 0.5
  polling_supported: false
  cancellable: false
  idempotent: true
  retry:
    safe: true
    maximum_attempts: 2
    backoff_s: 0.2
```

### 21.1 Timeout

A timeout shall be declared for every device-facing capability.

### 21.2 Stabilization

A capability that changes a physical condition shall declare stabilization behavior separately from protocol completion.

### 21.3 Idempotency

The model shall declare whether repeating an invocation with identical arguments is expected to produce an equivalent safe state.

### 21.4 Cancellation

Long-running capabilities shall declare whether they can be cancelled and which capability performs cancellation.

---

## 22. Merge and Precedence Rules

The effective capability model shall be created using this precedence, from highest to lowest:

1. validated live device data;
2. validated configured profile data;
3. static driver capability data;
4. explicit unknown value.

Live data shall not override a static safety restriction with a less restrictive value unless the static model explicitly permits that override.

The merged record shall retain provenance for overridden fields.

Example:

```yaml
maximum: 20.0
provenance:
  source: live
  supersedes:
    source: static
    value: 60.0
  reason: Detected module N6775A limit.
```

When sources conflict and no safe deterministic rule exists, the effective value shall be marked unknown or use the more restrictive safe limit.

---

## 23. Risk and Safety Metadata

Each executable capability shall define a risk level:

- `none`;
- `low`;
- `medium`;
- `high`;
- `critical`.

Example:

```yaml
risk:
  level: high
  categories: [energize_output, overcurrent]
  confirmation_required: true
  operator_required: false
  safe_in_simulation: true
  forbidden_when:
    - condition: safety.interlock_closed
      equals: false
  safe_defaults:
    voltage: 0.0
    current_limit: 0.01
```

### 23.1 Mandatory critical-operation metadata

Capabilities involving firmware updates, calibration writes, factory reset, data erasure, hazardous output, mechanism motion, or safety bypass shall define:

- confirmation requirement;
- required role or policy;
- interlocks;
- reversible/irreversible classification;
- recovery or rollback method;
- required cleanup;
- prohibited states.

### 23.2 Emergency capability

When a device supports a safe immediate shutdown, the model should expose:

```text
safety.emergency_stop.execute
```

or an equivalent standard safety capability.

---

## 24. Dependencies and Conflicts

A capability may depend on:

- another capability;
- optional Python package;
- transport type;
- device option;
- firmware version;
- module model;
- connected fixture;
- operator action;
- safety state;
- resource availability.

Example:

```yaml
dependencies:
  - type: capability
    id: connection.session.open
  - type: feature
    id: device.option.arb
    equals: true

conflicts:
  - type: resource
    id: acquisition.engine
    when_access: exclusive_operation
  - type: capability_state
    id: firmware.update.execute
    state: running
```

Dependencies shall be structured wherever possible.

---

## 25. Capability Composition

A capability binding may use one of four binding types:

| Type | Meaning |
|---|---|
| `direct` | One capability maps directly to one public keyword. |
| `adapter` | One capability maps to a compatibility adapter keyword. |
| `composed` | One capability is implemented by an ordered sequence of public keywords. |
| `virtual` | Capability is calculated or represented without a direct device action. |

A composed capability shall declare its steps:

```yaml
binding:
  type: composed
  executable: true
  steps:
    - capability_id: source.voltage.set
      argument_map:
        channel: $.channel
        voltage: $.voltage
    - capability_id: source.output.enable
      argument_map:
        channel: $.channel
```

Composed capabilities shall define failure cleanup and partial-execution behavior.

---

## 26. Query and Filtering Model

`Find Driver Capabilities` shall support structured filtering by at least:

- capability ID or prefix;
- category/domain;
- support state;
- current availability;
- risk level;
- resource type or resource ID;
- argument quantity or unit;
- return quantity or unit;
- standard or vendor-specific status;
- deprecated status;
- tag;
- free-text search over display name and description.

Example Robot Framework usage:

```robotframework
${caps}=    Find Driver Capabilities
...    category=measure
...    available=${TRUE}
...    return_quantity=electric_potential
...    maximum_risk=low
```

The query shall return an empty list when no capabilities match. It shall not fail solely because there are no matches.

Exact lookup by capability ID shall fail clearly when the ID is unknown unless the caller requests a nullable result.

---

## 27. Channel and Subsystem Discovery

Drivers with channels or modular subsystems shall expose them as resources and features.

A channel record should include:

```yaml
resource_id: channel.1
type: channel
index: 1
name: Channel 1
label: Main output
present: true
enabled: false
module:
  manufacturer: Keysight
  model: N6775A
  serial_number: null
capabilities:
  - source.voltage.set
  - source.current_limit.set
  - measure.voltage.dc
limits:
  voltage:
    minimum: 0.0
    maximum: 20.0
    unit: V
```

Capabilities with channel-dependent limits shall support either:

- resource-specific capability records; or
- argument constraints indexed by channel/resource.

A generic application shall not assume all channels are identical.

---

## 28. Capability Lifecycle and Compatibility

Each capability shall contain lifecycle metadata:

```yaml
lifecycle:
  introduced_in: "26.01"
  changed_in: "26.03"
  deprecated: false
  deprecated_in: null
  removal_planned_in: null
  replacement_capability_id: null
  compatibility: backward_compatible
```

### 28.1 Compatibility classifications

Allowed classifications are:

- `backward_compatible`;
- `behavior_extended`;
- `constraint_tightened`;
- `constraint_relaxed`;
- `return_extended`;
- `breaking`.

### 28.2 Stable identifiers

A keyword rename shall not require a capability ID change when semantics remain compatible.

A semantic breaking change shall use a new capability ID or a versioned capability variant when both behaviors must coexist.

### 28.3 Aliases

Keyword aliases shall be declared in the binding. Capability aliases, when unavoidable, shall be declared separately and resolve to one canonical capability ID.

---

## 29. Provenance and Freshness

Every field whose value may vary by connection, configuration, module, firmware, or device state shall expose provenance directly or through inherited record-level metadata.

Allowed source values are:

- `static`;
- `configured`;
- `live`;
- `calculated`;
- `cached_live`;
- `operator`;
- `unknown`.

Live and cached values shall include:

- acquisition timestamp;
- device identity used;
- validity period or stale flag;
- query or capability used to obtain the value where practical.

A capability snapshot from one device shall not be reused for a different detected device identity without being marked stale and refreshed.

---

## 30. Error Model

Discovery operations shall use the standard RFDS exception model and return structured validation data where requested.

The model shall distinguish:

- schema error;
- binding error;
- unknown capability;
- unsupported capability;
- currently unavailable capability;
- live discovery timeout;
- identity mismatch;
- stale model;
- conflicting discovery sources;
- unsafe discovery operation;
- optional dependency missing.

Example validation result:

```yaml
valid: false
errors:
  - code: CAP_BINDING_KEYWORD_MISSING
    capability_id: measure.voltage.dc
    message: Bound Robot Framework keyword was not exported.
warnings:
  - code: CAP_LIVE_DISCOVERY_SKIPPED
    message: Device was not connected; static model only.
```

A validation warning shall not be silently converted into success when it invalidates a mandatory field.

---

## 31. Validation Requirements

`Validate Driver Capabilities` shall verify at least:

1. schema validity;
2. unique capability IDs;
3. valid taxonomy format;
4. all mandatory fields;
5. valid argument and return schemas;
6. valid units and constraints;
7. minimum not greater than maximum;
8. defaults within declared constraints;
9. enum uniqueness;
10. valid support and availability states;
11. valid risk levels;
12. valid capability references;
13. valid resource references;
14. no unresolved dependency cycles unless explicitly supported;
15. executable capability bindings reference exported public keywords;
16. declared keyword signatures are compatible with capability arguments;
17. declared return metadata is compatible with the public contract;
18. aliases resolve correctly;
19. deprecated capabilities identify a replacement or explicit no-replacement reason;
20. discovery output is JSON serializable.

Validation shall return a machine-readable result and shall be usable as a release-gate test.

---

## 32. Binding Verification

Every executable capability shall be traceable to a public Robot Framework keyword.

The binding validator shall compare the capability model against deterministic Robot Framework library metadata obtained by Libdoc, runtime library introspection, or an equivalent mechanism.

The validator shall detect:

- missing bound keyword;
- normalized keyword-name collision;
- incompatible argument count;
- missing required argument metadata;
- incorrect default;
- undocumented alias;
- capability bound to a private helper;
- non-Robot-compatible return declaration;
- stale binding after keyword rename or removal.

RFDS-013 binding validation proves discoverability and metadata consistency. RFDS-019 proves callability and protocol behavior.

---

## 33. Runtime Discovery Safety

Live discovery shall be read-only unless a state change is unavoidable and explicitly approved.

The driver shall not perform the following merely to populate the capability model:

- energize an output;
- close an external relay path;
- move a mechanism;
- change calibration;
- erase files;
- update firmware;
- factory reset;
- alter safety limits;
- override an interlock;
- execute a self-test that can disturb a connected DUT without explicit permission.

Any live discovery action with side effects shall:

- be opt-in;
- declare the side effect;
- declare risk;
- define restoration behavior;
- record evidence.

---

## 34. Caching and Refresh

### 34.1 Static cache

Static driver capability information may be loaded once per driver version.

### 34.2 Live cache

Live discovery data may be cached only when:

- device identity is recorded;
- timestamp is recorded;
- staleness rules are defined;
- reconnect or identity change invalidates the cache;
- the caller can request a forced refresh.

### 34.3 Refresh behavior

`Refresh Driver Capabilities` shall support:

```text
static
configured
live
effective
```

A live refresh shall clearly report partial success when some device queries fail.

---

## 35. Minimal Standard Capability Set

Every driver shall expose the capabilities that are applicable to its device class.

The following capabilities are mandatory when the corresponding function exists:

```text
connection.session.open
connection.session.close
connection.session.status
identity.device.read
identity.driver.read
system.error.read
system.error.clear
system.reset.execute
system.self_test.execute
safety.output.disable_all
```

A driver shall not invent a nonfunctional implementation only to satisfy this list. Non-applicable capabilities shall be absent or explicitly `unsupported` according to project policy.

At minimum, every driver shall expose:

```text
identity.driver.read
```

and its RFDS-013 discovery capabilities.

---

## 36. Example Capability — Voltage Source

```yaml
capability_id: source.voltage.set
display_name: Set DC Voltage
description: Set the programmed voltage on one output channel.
category: source
standard: true
support:
  state: supported
  reason: null
  confidence: confirmed
binding:
  executable: true
  type: direct
  robot_keyword: Set DC Voltage
  canonical_keyword: Set DC Voltage
  aliases: [Program Voltage]
  python_method: set_dc_voltage
  library: rf_keysight_n6700.KeysightN6700Library
arguments:
  - name: channel
    position: 1
    required: true
    type: channel
    robot_type: integer
    minimum: 1
    maximum_feature: channel.count
    allow_none: false
    semantic_role: target
  - name: voltage
    position: 2
    required: true
    type: number
    robot_type: float
    unit: V
    quantity: electric_potential
    minimum: 0.0
    maximum_by_resource: source.voltage.maximum
    resolution_by_resource: source.voltage.resolution
    allow_none: false
    semantic_role: setpoint
returns: []
preconditions:
  - condition: driver.connected
    equals: true
    satisfaction_capability: connection.session.open
  - condition: firmware.update_active
    equals: false
postconditions:
  - condition: channel.{channel}.voltage_setpoint
    equals_argument: voltage
side_effects:
  - type: programmed_state_change
    target: channel.{channel}
    persistent_after_call: true
availability:
  available: true
  state: ready
timing:
  timeout_s: 10
  typical_duration_s: 0.15
  stabilization_s: 0.0
  idempotent: true
  cancellable: false
  retry:
    safe: true
    maximum_attempts: 2
risk:
  level: medium
  categories: [output_configuration]
  confirmation_required: false
resources:
  - resource_id: channel.{channel}
    access: exclusive_write
  - resource_id: transport.session
    access: shared
dependencies:
  - type: capability
    id: connection.session.open
conflicts:
  - type: capability_state
    id: firmware.update.execute
    state: running
cleanup:
  required: false
provenance:
  source: effective
lifecycle:
  introduced_in: "26.01"
  deprecated: false
  compatibility: backward_compatible
```

---

## 37. Example Capability — Measurement

```yaml
capability_id: measure.voltage.dc
display_name: Measure DC Voltage
description: Perform a DC voltage measurement and return the measured value.
category: measure
standard: true
support:
  state: supported
  confidence: confirmed
binding:
  executable: true
  type: direct
  robot_keyword: Measure DC Voltage
  canonical_keyword: Measure DC Voltage
  aliases: []
  python_method: measure_dc_voltage
arguments:
  - name: channel
    position: 1
    required: false
    default: 1
    type: channel
    robot_type: integer
    minimum: 1
    maximum_feature: channel.count
  - name: samples
    position: 2
    required: false
    default: 1
    type: integer
    robot_type: integer
    minimum: 1
    maximum: 1000
returns:
  - name: voltage
    type: number
    robot_type: float
    unit: V
    quantity: electric_potential
    value_origin: measured
    nullable: false
preconditions:
  - condition: driver.connected
    equals: true
availability:
  available: true
  state: ready
timing:
  timeout_s: 30
  typical_duration_s: 0.5
  maximum_duration_s: 30
  stabilization_s: 0.0
  idempotent: false
  cancellable: false
  retry:
    safe: true
    maximum_attempts: 2
risk:
  level: low
  categories: [measurement]
resources:
  - resource_id: acquisition.engine
    access: exclusive_operation
  - resource_id: channel.{channel}
    access: read
cleanup:
  required: false
```

---

## 38. Example Robot Framework Discovery Workflow

```robotframework
*** Settings ***
Library    rf_keysight_n6700

*** Test Cases ***
Discover Safe Voltage Measurement Capability
    ${model}=    Get Capability Model    mode=static
    ${matches}=    Find Driver Capabilities
    ...    capability_id=measure.voltage.dc
    ...    maximum_risk=low
    Should Not Be Empty    ${matches}

    Connect To Instrument    TCPIP0::192.168.0.10::inst0::INSTR
    ${model}=    Refresh Driver Capabilities    mode=effective
    ${cap}=    Get Driver Capability    measure.voltage.dc
    Should Be True    ${cap}[availability][available]
    ${voltage}=    Measure DC Voltage    channel=1
    Log    Measured voltage: ${voltage} V
    [Teardown]    Disconnect From Instrument
```

---

## 39. Generic Application Behavior

A generic application using RFDS-013 should:

1. load static discovery before connection;
2. validate schema compatibility;
3. show only supported capabilities by default;
4. distinguish unavailable from unsupported;
5. use display names for operators and IDs for internal logic;
6. render controls from structured argument metadata;
7. enforce declared ranges before invoking a keyword;
8. show units and enumerations explicitly;
9. request confirmation for high- and critical-risk operations;
10. honour resource conflicts and preconditions;
11. refresh live capabilities after connection, module change, firmware update, reset, or reconnect;
12. invalidate stale device-derived limits;
13. execute declared cleanup when an operation fails or a workflow ends;
14. store the capability-model version with generated tests or plans;
15. fail safely when required metadata is unknown.

The application shall not infer safety from the absence of risk metadata. Missing mandatory risk metadata is a model validation error.

---

## 40. Acceptance Criteria

A driver passes RFDS-013 only when:

1. the mandatory capability artifacts exist;
2. the capability model validates against the declared schema;
3. capability IDs are unique and stable;
4. all executable capabilities bind to exported public Robot Framework keywords;
5. all bindings have compatible signatures;
6. all arguments declare required type and constraint metadata;
7. all physical values declare units and quantities where applicable;
8. all return values declare Robot Framework-compatible types;
9. support state and current availability are distinguishable;
10. static discovery works without a connected device;
11. configured and live discovery clearly identify their source;
12. unknown values are explicit and are not reported as supported facts;
13. live discovery performs no undeclared hazardous side effect;
14. channel- or module-dependent limits are represented correctly;
15. safety-relevant capabilities contain risk, precondition, and cleanup metadata;
16. capability query and exact lookup operations work deterministically;
17. capability output is JSON serializable;
18. model freshness and device identity are traceable;
19. deprecated and aliased capabilities are declared;
20. validation evidence is generated for the release.

---

## 41. Failure Conditions

RFDS-013 shall fail when:

- a generic application must inspect source code to discover a supported standard capability;
- a capability exists only as an undocumented keyword name;
- an executable capability binds to a missing or private keyword;
- capability IDs collide or change without semantic reason;
- argument ranges, units, types, or required status are materially ambiguous;
- a physical value has no unit and is not explicitly dimensionless;
- a driver reports unsupported or unverified functionality as supported;
- current unavailability is incorrectly reported as permanent lack of support;
- live discovery performs an undeclared state-changing or hazardous operation;
- device-derived capability data is reused after identity change without invalidation;
- a channel-dependent limit is presented as global when channels differ;
- high-risk operations lack confirmation or safety metadata;
- a required cleanup action is omitted;
- the model cannot be serialized to JSON;
- validation cannot trace an executable capability to a public keyword;
- static discovery requires physical hardware;
- breaking capability changes are released without lifecycle metadata updates.

---

## 42. Evidence and Reporting

Each capability validation run shall produce:

```text
results/capability_model/<driver>/<timestamp>/
├── capability_model_static.json
├── capability_model_effective.json          # when live/configured discovery runs
├── capability_validation.json
├── capability_binding_matrix.csv
├── capability_diff.json                     # when compared with previous release
├── environment.json
├── device_identity.json                     # when connected
├── output.xml
├── log.html
├── report.html
└── capability_summary.md
```

The binding matrix shall contain at least:

| Field | Requirement |
|---|---|
| Capability ID | Stable machine identifier. |
| Display name | Human-readable name. |
| Standard/vendor | Classification. |
| Support state | Effective support status. |
| Availability | Current availability. |
| Robot keyword | Bound public keyword. |
| Python method | Implementation target. |
| Arguments valid | PASS/FAIL. |
| Returns valid | PASS/FAIL. |
| Risk metadata valid | PASS/FAIL. |
| Resource references valid | PASS/FAIL. |
| Live verified | PASS/FAIL/SKIP/N/A. |
| Result | PASS/FAIL/SKIP. |
| Evidence | Report or trace reference. |

---

## 43. Change Control

Whenever a public feature, keyword, supported model, option, channel, range, unit, return schema, side effect, safety rule, dependency, or availability rule changes, the same driver revision shall update:

- static capability model;
- schema extension when required;
- Robot Framework binding;
- feature metadata;
- lifecycle metadata;
- capability examples;
- capability validation tests;
- RFDS-017 AI Driver Contract where semantics are affected;
- RFDS-019 protocol vectors where invocation or protocol behavior is affected;
- README and GitHub Pages capability documentation;
- `history/` change description;
- `review/` capability-model review.

A capability-affecting code change without the corresponding RFDS-013 update shall fail release review.

---

## 44. Integration with Other RFDS Specifications

### 44.1 RFDS-002 — Public API

RFDS-002 defines mandatory public keyword naming and signatures. RFDS-013 exposes those keywords as machine-readable capability bindings.

### 44.2 RFDS-003 — BaseInstrumentLibrary

RFDS-003 should provide common discovery implementation, model loading, validation, caching, and refresh behavior.

### 44.3 RFDS-005 — Package Specification

RFDS-005 defines the final required location of capability artifacts in every driver package.

### 44.4 RFDS-007 — Error and Exception Standard

RFDS-007 defines exceptions raised by discovery, validation, unavailable capability use, and stale or conflicting models.

### 44.5 RFDS-009 — Testing Standard

RFDS-009 defines unit, simulator, integration, and hardware testing required for capability discovery.

### 44.6 RFDS-010 — Driver Review Checklist

RFDS-010 shall include capability accuracy, binding integrity, safety metadata, compatibility, and evidence review.

### 44.7 RFDS-011 — Release Process

RFDS-011 shall require capability-model validation and a capability diff before release.

### 44.8 RFDS-017 — AI Driver Contract

RFDS-013 is the concise runtime discovery model for generic applications. RFDS-017 is the richer AI-readable semantic contract for one driver.

The two specifications shall agree on:

- capability identity;
- canonical keyword;
- arguments and returns;
- preconditions and postconditions;
- side effects;
- timing;
- risk;
- resources;
- limitations;
- errors.

RFDS-017 may contain planning and verification semantics that are intentionally outside RFDS-013.

### 44.9 RFDS-018 — AI Test Bench Contract

RFDS-018 may aggregate RFDS-013 capabilities and resources from multiple installed drivers to determine what the bench can perform at runtime.

### 44.10 RFDS-019 — Driver Call and Protocol Conformance

RFDS-019 shall verify that the public keyword bound to an executable capability can be called through Robot Framework and produces the declared protocol behavior.

RFDS-013 validates **what is discoverable and how it is described**. RFDS-019 validates **that the declared public call reaches the intended device protocol operation**.

---

## 45. Implementation Lifecycle Placement

RFDS-013 shall be maintained through every implementation phase:

### Gate 1 — Architecture and Skeleton

- create capability directory and schema;
- define initial taxonomy and IDs;
- implement static discovery skeleton;
- define common discovery interfaces.

### Gate 2 — Core Implementation

- bind implemented public keywords;
- define arguments, returns, states, and resources;
- add model and binding unit tests.

### Gate 3 — Extended Features

- add live discovery;
- add channel/module-dependent constraints;
- add dependencies, conflicts, and dynamic availability;
- update AI metadata.

### Gate 4 — Tests and Documentation

- run schema, binding, configured, simulator, and live-device tests;
- publish capability documentation and examples;
- generate evidence reports.

### Gate 5 — Review and Release

- review capability accuracy and safety;
- compare capability model with the previous release;
- resolve breaking changes;
- include updated capability artifacts in the release ZIP.

---

## 46. Review Checklist

1. Can the model be loaded without connecting hardware?
2. Does every capability have a stable ID?
3. Are standard capabilities used instead of unnecessary vendor-specific IDs?
4. Is support distinct from current availability?
5. Are unsupported and unknown states represented honestly?
6. Does every executable capability bind to an exported Robot Framework keyword?
7. Do keyword signatures match argument metadata?
8. Are aliases and deprecated keywords declared?
9. Do all physical values have units and quantities?
10. Are ranges, defaults, resolution, and enumerations structured?
11. Are channel- and module-dependent limits represented?
12. Are return values Robot Framework-compatible and documented?
13. Are preconditions, postconditions, and side effects explicit?
14. Are timing, timeout, stabilization, retry, and idempotency defined?
15. Are resources and conflicts usable by an orchestrator?
16. Are high-risk and critical capabilities marked and protected?
17. Does live discovery avoid hazardous state changes?
18. Is provenance retained for static, configured, and live fields?
19. Are cache invalidation and freshness rules correct?
20. Do exact lookup and structured filtering work?
21. Is JSON serialization lossless?
22. Does validation detect stale or broken keyword bindings?
23. Does the capability diff identify breaking changes?
24. Does RFDS-017 agree with RFDS-013?
25. Does RFDS-019 cover executable capability bindings?

---

## 47. Minimum Definition of Done

RFDS-013 implementation for a driver is complete when:

- the static capability model exists and validates;
- the mandatory discovery interfaces are callable through Robot Framework;
- all implemented standard functions have stable capability IDs;
- all executable capabilities are bound to public keywords;
- all required metadata is complete;
- static discovery works offline;
- configured and live discovery work where applicable;
- live discovery is safe and traceable;
- runtime availability is represented;
- channel and module variations are represented;
- safety and cleanup metadata are complete;
- capability validation and binding tests pass;
- required evidence files are generated;
- the capability model is included in README/GitHub Pages documentation;
- `history/` and `review/` contain the revision evidence;
- no mandatory capability-model verification remains NOT RUN without an approved reason.

---

## 48. Goal

Provide a stable, safe, machine-readable model that allows generic applications to discover, present, validate, and invoke RFDS driver features without device-specific source-code knowledge or hard-coded keyword mappings.

---

## Appendix A — Recommended Standard Capability IDs

The following list is non-exhaustive. Drivers shall use applicable IDs and may propose additions through RFDS change control.

### Connection

```text
connection.session.open
connection.session.close
connection.session.reconnect
connection.session.status
connection.device.detect
connection.device.list
connection.timeout.get
connection.timeout.set
```

### Identity

```text
identity.driver.read
identity.device.read
identity.firmware.read
identity.modules.list
identity.options.list
```

### System

```text
system.error.read
system.error.clear
system.status.read
system.health.read
system.self_test.execute
system.reset.execute
system.local.execute
system.remote.execute
system.operation.wait
```

### Source

```text
source.output.enable
source.output.disable
source.output.disable_all
source.voltage.set
source.voltage.read
source.current.set
source.current.read
source.current_limit.set
source.power_limit.set
source.frequency.set
source.waveform.configure
source.waveform.start
source.waveform.stop
```

### Measurement

```text
measure.voltage.dc
measure.voltage.ac
measure.current.dc
measure.current.ac
measure.resistance.two_wire
measure.resistance.four_wire
measure.frequency
measure.period
measure.power.dc
measure.temperature
measure.continuity
measure.diode
```

### Load

```text
load.input.enable
load.input.disable
load.mode.set
load.current.set
load.voltage.set
load.resistance.set
load.power.set
load.transient.configure
load.transient.start
load.transient.stop
```

### Switching

```text
switch.relay.open
switch.relay.close
switch.relay.state.read
switch.all.open
switch.route.set
switch.route.read
switch.matrix.connect
switch.matrix.disconnect
```

### Trigger and acquisition

```text
trigger.source.set
trigger.level.set
trigger.arm
trigger.initiate
trigger.abort
trigger.status.read
acquisition.configure
acquisition.start
acquisition.stop
acquisition.status.read
acquisition.data.read
acquisition.buffer.clear
```

### Safety

```text
safety.interlock.read
safety.limits.read
safety.limits.set
safety.output.disable_all
safety.emergency_stop.execute
safety.safe_state.execute
```

### Calibration, files, and firmware

```text
calibration.status.read
calibration.data.read
calibration.data.write
calibration.start
calibration.abort
file.device.list
file.device.upload
file.device.download
file.device.delete
firmware.version.read
firmware.update.execute
firmware.rollback.execute
```

### Diagnostics and logging

```text
logging.driver.start
logging.driver.stop
logging.driver.export
logging.device.read
logging.trace.start
logging.trace.stop
logging.trace.export
system.diagnostics.read
```

---

## Appendix B — Minimum Static Capability Model Example

```yaml
schema:
  name: rfds-capability-model
  version: "1.0"

driver:
  id: rf_example_meter
  name: Example Meter Driver
  version: "26.01"
  api_version: "1.0"
  capability_model_version: "1.0"

source:
  discovery_mode: static
  generated_at: null
  connected: false
  stale: false

identity:
  manufacturer: null
  model: null
  serial_number: null
  firmware_version: null

features:
  transport.supported:
    value: [visa, tcpip]
    type: list
    source: static
    confidence: declared

resources:
  - resource_id: instrument.main
    type: instrument
    display_name: Main instrument
    state: unknown

capabilities:
  - capability_id: identity.driver.read
    display_name: Get Driver Information
    description: Return driver identity and version information.
    category: identity
    standard: true
    support:
      state: supported
      reason: null
      confidence: declared
    binding:
      executable: true
      type: direct
      robot_keyword: Get Driver Information
      canonical_keyword: Get Driver Information
      aliases: []
      python_method: get_driver_information
      library: rf_example_meter.ExampleMeterLibrary
    arguments: []
    returns:
      - name: driver_information
        type: object
        robot_type: dictionary
        schema_ref: driver_identity_v1
        nullable: false
    preconditions: []
    postconditions: []
    side_effects: []
    availability:
      available: true
      state: ready
      reason: null
    timing:
      timeout_s: 1
      typical_duration_s: 0.01
      stabilization_s: 0
      idempotent: true
      cancellable: false
      retry:
        safe: true
        maximum_attempts: 1
    risk:
      level: none
      categories: []
      confirmation_required: false
    resources: []
    dependencies: []
    conflicts: []
    cleanup:
      required: false
    provenance:
      source: static
    lifecycle:
      introduced_in: "26.01"
      deprecated: false
      compatibility: backward_compatible

validation:
  valid: true
  errors: []
  warnings: []

extensions: {}
```

---

## Appendix C — RFDS-013 and RFDS-017 Information Boundary

| Information | RFDS-013 | RFDS-017 |
|---|---:|---:|
| Capability ID | Mandatory | Mandatory reference |
| Runtime availability | Mandatory | May consume |
| Keyword binding | Mandatory | Mandatory |
| Arguments and returns | Mandatory concise schema | Mandatory detailed semantics |
| Units and constraints | Mandatory | Mandatory |
| State preconditions | Mandatory | Mandatory, richer model |
| Side effects and risk | Mandatory | Mandatory |
| Timing and resources | Mandatory | Mandatory |
| Error catalogue | Capability-relevant summary | Full driver catalogue |
| Planning hints | Out of scope | Mandatory |
| Verification objectives | Reference only | Mandatory |
| Multi-step test synthesis semantics | Out of scope | In scope |
| Runtime feature filtering | Mandatory | Optional |
| Generic GUI control generation | Primary use case | Secondary use case |
| AI test-plan generation | Supporting input | Primary use case |

---

## Appendix D — Version 1.0 Design Decisions

Version 1.0 establishes:

- a stable capability-ID taxonomy;
- mandatory static discovery;
- optional configured and live discovery merged into an effective model;
- standardized support and availability states;
- structured arguments, returns, units, constraints, resources, risk, timing, and lifecycle data;
- public Robot Framework and Python discovery interfaces;
- safe live discovery rules;
- deterministic validation and binding verification;
- explicit integration boundaries with RFDS-017, RFDS-018, and RFDS-019.
