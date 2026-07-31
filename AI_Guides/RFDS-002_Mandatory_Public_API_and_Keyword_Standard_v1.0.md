# RFDS-002 — Mandatory Public API and Robot Framework Keyword Standard

**Version:** 1.0  
**Document ID:** RFDS-002  
**Status:** Draft project requirement  
**Applies to:** All RFDS Robot Framework driver packages  

---

## 1. Purpose

This specification defines the mandatory public API, Robot Framework keyword conventions, signatures, return types, error behavior, compatibility rules, and documentation requirements for every RFDS driver.

The standard has four goals:

1. make different hardware drivers predictable to human test developers;
2. make public keywords safe and unambiguous for AI-generated test plans;
3. provide a stable contract that can be inventoried and tested automatically;
4. prevent private helpers, transport details, and accidental methods from becoming public Robot Framework keywords.

The canonical public interface of an RFDS driver is its exported Robot Framework keyword set. A Python API may also be provided, but it shall not contradict the Robot Framework API defined here.

---

## 2. Scope

### 2.1 In scope

RFDS-002 covers:

- public Robot Framework keyword discovery;
- mandatory universal driver keywords;
- conditional capability keyword groups;
- canonical keyword names and aliases;
- Python implementation method naming;
- keyword signatures, arguments, defaults, and type conversion;
- return values and Robot Framework-compatible data types;
- connection and session semantics;
- state, safety, timeout, retry, and error behavior;
- keyword documentation and metadata;
- API compatibility, deprecation, and removal;
- public API inventory and machine-readable API declaration;
- API-level acceptance criteria.

### 2.2 Out of scope

RFDS-002 does not define:

- device-specific protocol commands or frame formats;
- complete vendor-manual feature coverage;
- physical measurement accuracy;
- calibration accuracy;
- package layout outside API-related artifacts;
- detailed code architecture;
- the complete AI contract schema;
- bench topology or multi-instrument planning;
- protocol conformance execution details.

Those subjects are covered by device-specific requirements and other RFDS specifications.

---

## 3. Normative terminology

- **shall / shall not** — mandatory requirement;
- **should / should not** — recommended requirement; deviations require documented justification;
- **may** — permitted implementation choice;
- **canonical keyword** — the primary supported public keyword name;
- **alias** — an additional public keyword name mapped to a canonical keyword;
- **device-facing keyword** — a keyword that causes or may cause a transport, protocol, SDK, GPIO, or physical-device operation;
- **query keyword** — a keyword that obtains data without intentionally changing device state;
- **command keyword** — a keyword that intentionally changes driver or device state;
- **dangerous keyword** — a keyword capable of creating an unsafe electrical, mechanical, thermal, data-loss, or equipment-damage condition.

---

## 4. Public API layers

An RFDS driver may contain the following layers:

```text
Robot Framework test
        ↓
canonical public Robot Framework keywords
        ↓
public or internal Python adapter methods
        ↓
validated device-domain service
        ↓
transport / vendor SDK / protocol implementation
        ↓
physical device or approved simulator
```

Only the canonical Robot Framework keyword layer is mandatory for every driver.

### 4.1 Canonical Robot Framework API

The canonical API shall:

- be explicitly declared;
- be discoverable using Robot Framework Libdoc or equivalent introspection;
- expose only supported public operations;
- use stable keyword names and signatures;
- return Robot Framework-compatible values;
- be represented in the RFDS-017 AI Driver Contract;
- be covered by RFDS-019 call and protocol conformance tests.

### 4.2 Public Python API

A driver may expose a public Python API for direct Python users.

When provided:

- public Python methods should map one-to-one to canonical Robot Framework keywords where practical;
- method names shall use `snake_case`;
- argument names, defaults, return values, and exceptions shall remain semantically equivalent to the Robot Framework API;
- public Python methods shall be documented separately from private helpers;
- private transport and parsing methods shall start with `_` or reside in non-public implementation modules.

### 4.3 Internal APIs

Internal helpers, transport methods, protocol encoders, parsers, caches, fixtures, and test hooks are not part of the public API unless explicitly declared.

Internal methods shall not be treated as stable or callable from Robot Framework.

---

## 5. Mandatory library declaration

Each Python-based RFDS library shall explicitly configure Robot Framework library behavior.

A static library should use the equivalent of:

```python
from robot.api.deco import keyword, library

@library(
    scope="SUITE",
    version=__version__,
    auto_keywords=False,
)
class ExampleDriverLibrary:
    ...
```

Mandatory rules:

1. automatic keyword discovery shall be disabled;
2. every public keyword shall be explicitly decorated or otherwise explicitly registered;
3. the library version shall be exposed to Robot Framework;
4. the library scope shall be explicitly declared;
5. library construction shall not open hardware connections or change device state;
6. all device I/O shall occur only after an explicit public connection or setup operation;
7. helper methods shall not become keywords accidentally.

### 5.1 Library scope

The driver shall declare one of the supported Robot Framework scopes and document the reason.

- `SUITE` is the default recommendation for stateful hardware drivers because it limits state leakage between suites.
- `GLOBAL` may be used when one physical resource must be shared across multiple suites in the same execution.
- `TEST` should be used only when opening and closing a session for every test is safe, efficient, and intended.

Regardless of scope, `Disconnect` shall be safe to call during teardown.

---

## 6. Keyword exposure rules

A callable shall be public only when all of the following are true:

1. it is explicitly registered as a Robot Framework keyword;
2. it has a canonical public name;
3. it has complete documentation;
4. it has a stable signature;
5. its arguments and return values are Robot Framework-compatible;
6. it is present in the public API inventory;
7. it is represented in the AI Driver Contract;
8. it has RFDS-019 callability coverage;
9. a device-facing keyword has a protocol vector or an approved exclusion.

The following shall not be exported:

- names beginning with `_`;
- low-level transport handles;
- raw vendor SDK objects;
- protocol encoder or parser helpers;
- debug-only methods;
- unit-test hooks;
- methods whose behavior is undocumented;
- duplicate names that collide after Robot Framework normalization.

---

## 7. Keyword naming standard

### 7.1 General form

Canonical keyword names shall:

- use readable Title Case in documentation and examples;
- start with a clear action verb;
- describe one primary operation;
- avoid unexplained abbreviations;
- avoid implementation-specific class or method names;
- avoid punctuation unless it is part of an established technical term;
- remain unique after case, spaces, and underscores are ignored;
- avoid embedding arguments in the keyword name unless explicitly approved.

Preferred:

```robotframework
Connect
Get Identity
Set DC Voltage
Measure DC Current
Enable Output
Open Relay
Upload Calibration File
Device Should Be Connected
```

Not permitted as canonical names:

```robotframework
Do Connect
Connect To DMM Device
set_dc_voltage
Voltage
Run Command
Send Data
Open ${channel} Relay
```

### 7.2 Verb semantics

The following verbs have standardized meanings:

| Verb | Required meaning |
|---|---|
| `Connect` | Establish a driver-to-device session. |
| `Disconnect` | Close a session and release associated resources. |
| `Check` | Perform a bounded diagnostic and return success data or fail with a diagnostic error. |
| `Get` | Return known state, configuration, metadata, or a queried value. It shall not imply a physical measurement trigger unless documented. |
| `Read` | Obtain available data or device state, normally through a device read/query operation. |
| `Measure` | Trigger or acquire a physical measurement. |
| `Set` | Change one primary value or state. |
| `Configure` | Apply a coherent group of settings. |
| `Enable` / `Disable` | Change a binary operating mode. |
| `Start` / `Stop` | Control a time-based, buffered, or asynchronous operation. |
| `Open` / `Close` | Control a relay, switch, path, valve, port, or similar domain object; not a transport session. |
| `Reset` | Restore a defined reset state. Potential side effects shall be explicit. |
| `Clear` | Remove or acknowledge stored state, errors, data, or status. |
| `Save` / `Load` | Persist to or restore from the driver, local system, or device as documented. |
| `Upload` / `Download` | Transfer data toward or away from the physical device. |
| `List` | Return zero or more items without changing them. |
| `Select` | Make an existing item, channel, or connection active. |
| `Should` | Assert a condition and fail the Robot Framework keyword when the condition is false. |

### 7.3 Device name in keyword names

Canonical keywords should not repeat the device or library name when the library context already identifies it.

Preferred:

```robotframework
N6700.Set DC Voltage    1    5.0
DMM.Measure DC Voltage
Relay.Open Relay        3
```

Avoid:

```robotframework
Set N6700 DC Voltage
Measure HP34401A DC Voltage
Open Phidget Relay
```

A device name may appear when required to distinguish two genuinely different concepts inside one library.

### 7.4 Acronyms and units

Established acronyms may retain conventional uppercase spelling, including:

- AC;
- DC;
- RF;
- RMS;
- IDN;
- IP;
- LAN;
- USB;
- VISA;
- SCPI;
- CAN;
- GPIO;
- NPLC.

Units shall not be hidden in ambiguous argument names. Units shall be included in Python argument names, documentation, and structured return fields using normalized suffixes such as:

- `_v` for volts;
- `_a` for amperes;
- `_ohm` for ohms;
- `_hz` for hertz;
- `_s` for seconds;
- `_ms` for milliseconds;
- `_c` for degrees Celsius where the domain clearly requires temperature;
- `_pct` for percent.

---

## 8. Mandatory universal keyword set

Every RFDS hardware driver shall implement the canonical keywords in this section.

### 8.1 `Connect`

**Purpose:** Establish a driver-to-device session.

Canonical signature:

```text
Connect(resource=None, alias="default", timeout_s=None, **options) -> dict
```

Mandatory behavior:

- validates arguments before transport activity where possible;
- establishes the requested session;
- performs a safe communication check when supported;
- does not change functional device outputs unless the connection protocol itself requires it;
- returns the normalized connection-state dictionary defined in Section 12;
- is idempotent when the same alias is already connected to the same resource and compatible options;
- shall not silently reconnect an alias to a different resource;
- shall fail with a state or validation error when an existing alias conflicts;
- shall redact credentials and secrets from logs and returned data.

`resource` is a normalized connection identifier. Examples include a VISA resource, serial port, IP address, hostname, SDK serial number, URL, or fixture-specific identifier.

### 8.2 `Disconnect`

Canonical signature:

```text
Disconnect(alias=None) -> None
```

Mandatory behavior:

- closes the specified or active session;
- releases locks, transport handles, worker threads, and temporary resources;
- is idempotent;
- does not fail merely because the requested alias is already disconnected;
- does not energize or reconfigure the device during cleanup;
- executes a documented safe-state action first when the device capability group requires it.

### 8.3 `Is Connected`

Canonical signature:

```text
Is Connected(alias=None) -> bool
```

Mandatory behavior:

- returns a real Boolean;
- does not raise merely because no session exists;
- does not perform a destructive or state-changing device operation;
- shall document whether it reports cached transport state or performs a live probe.

### 8.4 `Get Connection State`

Canonical signature:

```text
Get Connection State(alias=None, refresh=False) -> dict
```

Returns the normalized connection-state dictionary defined in Section 12.

When `refresh=True`, the driver shall perform a bounded safe probe if the transport and device support one.

### 8.5 `Check Communication`

Canonical signature:

```text
Check Communication(alias=None) -> bool
```

Mandatory behavior:

- performs a bounded, non-destructive communication operation;
- returns `True` when the communication check succeeds;
- raises a typed driver exception when the check cannot be completed;
- shall not return `False` for an unexplained transport or protocol failure;
- shall not change functional output state.

### 8.6 `Get Identity`

Canonical signature:

```text
Get Identity(alias=None, refresh=True) -> str
```

Mandatory behavior:

- returns a stable human-readable identity string;
- queries the device when a standard identity operation exists and `refresh=True`;
- may return a documented configured or SDK-derived identity when the device has no identity query;
- shall not return `None` on success;
- shall preserve the raw device identity in evidence when applicable.

### 8.7 `Get Driver Information`

Canonical signature:

```text
Get Driver Information() -> dict
```

The returned dictionary shall contain at least:

```yaml
name: rf_example
version: "26.01"
api_spec: RFDS-002
api_spec_version: "1.0"
robot_framework_min_version: "<declared version>"
python_min_version: "<declared version>"
library_scope: SUITE
transport_types:
  - scpi_tcp
capability_ids:
  - connection
  - identity
```

Additional fields may include package build, Git commit, vendor, model family, supported operating systems, and protocol version.

### 8.8 `Get Driver Capabilities`

Canonical signature:

```text
Get Driver Capabilities() -> list[str]
```

Returns stable machine-readable capability identifiers. Capability identifiers shall use lowercase `snake_case` and shall be declared in the RFDS-017 AI Driver Contract.

This keyword returns RFDS-002's flat, group-level capability names for quick discovery of which conditional keyword groups (Section 9) a driver implements; the return type shall remain `list[str]` for Robot Framework compatibility. RFDS-013 separately defines a hierarchical, dot-separated `capability_id` grammar (`<domain>.<object>.<operation>`) and a richer capability model carrying per-capability support state, availability, and metadata, exposed through the distinct `Get Capability Model` keyword. These are complementary, not competing: RFDS-013 is authoritative for the exact hierarchical identifier grammar and the full capability model, and the AI Driver Contract shall map each RFDS-002 group name below to its corresponding RFDS-013 `capability_id`. A driver shall not expose two independently-maintained capability catalogues that can drift apart.

Examples:

```text
connection
identity
multi_connection
error_queue
channel_selection
dc_voltage_source
dc_voltage_measurement
relay_control
file_transfer
safe_shutdown
raw_io
```

### 8.9 `Set Communication Timeout`

Canonical signature:

```text
Set Communication Timeout(timeout_s, alias=None) -> float
```

Mandatory behavior:

- validates a finite, positive timeout;
- applies the timeout to the selected session or documented driver default;
- returns the effective timeout in seconds;
- shall not silently clamp the value unless the applied value is returned and documented.

### 8.10 `Get Communication Timeout`

Canonical signature:

```text
Get Communication Timeout(alias=None) -> float
```

Returns the effective timeout in seconds.

---

## 9. Conditional capability keyword groups

A conditional keyword group becomes mandatory when the driver declares the corresponding capability.

The driver shall not declare a capability unless all mandatory keywords in its group are implemented or an explicit device-specific limitation is approved.

### 9.1 Multi-connection capability

Capability ID: `multi_connection`

Mandatory keywords:

```text
List Connections() -> list[dict]
Select Connection(alias) -> dict
Disconnect All() -> None
Get Active Connection() -> str | None
```

Rules:

- every session has a unique string alias;
- `default` is the default alias when no alias is supplied;
- device-facing operations shall clearly identify which connection they use;
- the active alias shall never change implicitly as a side effect of an unrelated keyword.

### 9.2 Device error-queue capability

Capability ID: `error_queue`

Mandatory keywords:

```text
Get Device Error(alias=None) -> dict
Get All Device Errors(alias=None, max_count=100) -> list[dict]
Clear Device Errors(alias=None) -> None
Device Error Queue Should Be Empty(alias=None) -> None
```

The error dictionary shall contain, where available:

```yaml
code: 0
message: No error
raw: '0,"No error"'
source: device
```

The driver shall prevent unbounded reads from an error queue.

### 9.3 Channel-selection capability

Capability ID: `channel_selection`

Mandatory keywords:

```text
List Channels(alias=None) -> list
Validate Channel(channel, alias=None) -> bool
```

`Select Channel` is mandatory only when the physical device has an active-channel concept. Drivers should prefer explicit `channel` arguments on functional keywords instead of relying on hidden active-channel state.

### 9.4 Output-control capability

Capability ID: `output_control`

Mandatory keywords:

```text
Enable Output(channel=None, alias=None) -> None
Disable Output(channel=None, alias=None) -> None
Get Output State(channel=None, alias=None) -> bool
Output Should Be Enabled(channel=None, alias=None) -> None
Output Should Be Disabled(channel=None, alias=None) -> None
```

Rules:

- Boolean output state shall be returned as `bool`;
- `Disable Output` shall be idempotent;
- output-enable operations shall be classified for safety and shall validate prerequisites before transmission;
- connection teardown shall define whether outputs remain unchanged or are placed into a safe state.

### 9.5 Source or setpoint capability

Typical capability IDs include `dc_voltage_source`, `dc_current_source`, `electronic_load`, `temperature_control`, and `resistance_simulation`.

Each settable quantity shall provide, as applicable:

```text
Set <Quantity>(value, channel=None, alias=None) -> None
Get <Quantity> Setpoint(channel=None, alias=None) -> float
Get <Quantity> Limits(channel=None, alias=None) -> dict
```

A driver shall not use `Get <Quantity>` when it would be ambiguous whether the result is a configured setpoint or a live measurement.

### 9.6 Measurement capability

Typical capability IDs include `dc_voltage_measurement`, `dc_current_measurement`, `resistance_measurement`, `frequency_measurement`, and `temperature_measurement`.

Each physical measurement shall provide:

```text
Measure <Quantity>(channel=None, alias=None, **options) -> float | dict
```

Rules:

- `Measure` shall represent a live acquisition or explicit measurement cycle;
- the returned unit shall be fixed and documented;
- a scalar is preferred for a single measurement value;
- a dictionary shall be used when status, timestamp, range, uncertainty, or multiple values are returned;
- no formatted unit string shall replace the numeric value.

### 9.7 Relay or switch capability

Capability ID: `relay_control`

Mandatory keywords:

```text
Open Relay(channel, alias=None) -> None
Close Relay(channel, alias=None) -> None
Set Relay State(channel, closed, alias=None) -> None
Get Relay State(channel, alias=None) -> bool
Open All Relays(alias=None) -> None
Get All Relay States(alias=None) -> dict
Relay Should Be Open(channel, alias=None) -> None
Relay Should Be Closed(channel, alias=None) -> None
```

Canonical Boolean meaning:

```text
False = open
True  = closed
```

The keywords `Open Relay` and `Close Relay` shall describe the electrical contact state, not the connection session state.

### 9.8 Reset capability

Capability ID: `device_reset`

Mandatory keyword:

```text
Reset Device(alias=None, wait_until_ready=True, timeout_s=None) -> dict
```

The documentation shall state:

- reset type;
- output behavior;
- settings preserved or cleared;
- reconnect behavior;
- expected ready time;
- safety risk.

### 9.9 File-transfer capability

Capability ID: `file_transfer`

Mandatory keywords, as applicable:

```text
List Device Files(path="/", alias=None) -> list[dict]
Upload File(local_path, device_path=None, overwrite=False, alias=None) -> dict
Download File(device_path, local_path=None, overwrite=False, alias=None) -> dict
Delete Device File(device_path, alias=None) -> None
```

Rules:

- local and device paths shall be distinguished explicitly;
- overwrite shall default to `False`;
- transferred byte count and final path shall be returned;
- destructive operations shall be clearly tagged;
- path traversal and unsafe local-path behavior shall be prevented.

### 9.10 Safe-shutdown capability

Capability ID: `safe_shutdown`

This capability is mandatory for drivers that can energize, load, heat, move, switch hazardous power, or otherwise create a persistent hazardous state.

Mandatory keyword:

```text
Safe Shutdown(alias=None, timeout_s=None) -> dict
```

Mandatory behavior:

- attempts the documented safe-state sequence;
- is idempotent;
- continues best-effort cleanup after an individual safe-state step fails;
- returns a structured result when all requested actions complete;
- raises `DriverSafetyError` when the safe state cannot be confirmed;
- shall be suitable for suite teardown and emergency cleanup.

### 9.11 Raw I/O capability

Capability ID: `raw_io`

Raw protocol keywords are optional and shall not replace domain-level keywords.

Permitted canonical names:

```text
Write Raw Command(command, alias=None) -> None
Query Raw Command(command, alias=None, timeout_s=None) -> str | bytes
Read Raw Response(alias=None, timeout_s=None) -> str | bytes
```

Rules:

- raw I/O shall be disabled by default or require explicit opt-in when it can bypass driver safety validation;
- keywords shall be tagged `rfds:raw_io` and `rfds:high_risk`;
- secrets shall be redacted;
- raw I/O shall not be presented as the primary public API;
- the AI Driver Contract shall warn that raw I/O may invalidate state tracking.

---

## 10. Keyword argument standard

### 10.1 Argument names

Python argument names shall:

- use `snake_case`;
- use domain terminology;
- include unit suffixes when the unit is not inherent in the parameter;
- use `channel` for a single channel identifier;
- use `channels` for a collection;
- use `alias` for a connection alias;
- use `timeout_s` for a timeout in seconds;
- use `resource` for a connection resource identifier;
- use `refresh` for an explicit live refresh instead of cached data;
- use `wait_until_ready` for a post-operation readiness wait;
- use `overwrite` for replacement of existing files or records;
- use `**options` only for genuinely transport- or model-specific options.

### 10.2 Positional and named arguments

- the most common required arguments shall appear first;
- optional arguments shall follow required arguments;
- safety-critical options should be named-only in Python where practical;
- examples shall demonstrate named arguments when multiple adjacent values have the same type or could be confused;
- adding a new optional argument at the end is backward-compatible;
- reordering existing arguments is a breaking API change.

### 10.3 Default values

Default values shall:

- be deterministic;
- be safe;
- be shown in Libdoc and the API inventory;
- not depend on hidden environment state unless explicitly documented;
- not enable output, overwrite files, clear data, or perform destructive actions;
- use `None` when the driver or profile default is intentionally selected.

### 10.4 Type annotations and conversion

Every public Python method shall use type annotations for all arguments and return values.

Supported public argument types should be limited to:

- `str`;
- `int`;
- `float`;
- `bool`;
- `None` / optional values;
- enums with documented accepted names;
- `list`, `tuple`, or `dict` when necessary;
- `pathlib.Path` only when Robot Framework conversion behavior is verified and documented.

The driver shall validate:

- numeric finiteness;
- numeric range;
- enum membership;
- channel existence;
- resource format;
- file path safety;
- state preconditions;
- mutually exclusive arguments.

Validation that can be performed locally shall occur before protocol transmission.

### 10.5 Boolean arguments

Boolean arguments shall use real Boolean semantics and shall not require device-specific text such as `ON`, `OFF`, `1`, or `0` from the Robot test author.

Protocol-specific serialization belongs inside the driver.

### 10.6 Enum arguments

Accepted enum values shall:

- use lowercase or documented case-insensitive names at the Python boundary;
- be normalized by the driver;
- be listed in keyword documentation and RFDS-017;
- reject unknown values before transmission.

### 10.7 Variable argument lists

Public keywords should avoid `*args` and unstructured `**kwargs` because they weaken Libdoc, AI-contract, and conformance precision.

`**options` may be used only when:

- all accepted keys are documented;
- unknown keys are rejected;
- each key has a declared type and default;
- protocol vectors cover the options that affect transmitted data.

---

## 11. Return value standard

### 11.1 Permitted return types

Public keywords shall return only Robot Framework-compatible values:

- `None`;
- `bool`;
- `int`;
- `float`;
- `str`;
- `bytes` only for explicitly documented binary operations;
- `list` or `tuple` containing compatible values;
- `dict` with string keys and compatible values.

The following shall not be returned directly:

- transport objects;
- VISA resources;
- serial objects;
- sockets;
- vendor SDK handles;
- generators;
- iterators requiring later transport activity;
- custom domain objects;
- exceptions as data;
- dataclasses unless converted to dictionaries first.

### 11.2 Command returns

A command keyword should return `None` when successful.

A command may return a normalized dictionary when the result provides material information, such as:

- actual applied value;
- selected range;
- operation identifier;
- file transfer result;
- reset readiness;
- safe-shutdown confirmation.

A driver shall not return arbitrary success strings such as `OK`, `Done`, or `Success` when normal completion already indicates success.

### 11.3 Query and measurement returns

- a single logical value should return a scalar;
- multiple named values shall return a dictionary;
- repeated homogeneous values shall return a list;
- numeric values shall remain numeric;
- units shall be fixed and documented rather than appended to numeric strings;
- timestamps shall use ISO 8601 strings with timezone information when returned as text.

### 11.4 Dictionary schema stability

Keys in public return dictionaries are part of the public API.

They shall:

- use lowercase `snake_case`;
- remain stable across compatible releases;
- be listed in documentation and `public_api.yaml`;
- not disappear without deprecation or a breaking-version change;
- use `None` for known but unavailable optional values rather than changing the schema unpredictably.

---

## 12. Standard data schemas

### 12.1 Connection-state schema

`Connect`, `Get Connection State`, `Select Connection`, and related keywords shall use the following normalized fields:

```yaml
alias: default
resource: TCPIP0::192.168.0.55::5025::SOCKET
connected: true
communication_ok: true
transport: scpi_tcp
identity: OpenBench,E-Resistor,SN001,0.8.0
connected_at: "2026-07-26T08:30:00+03:00"
last_communication_at: "2026-07-26T08:30:01+03:00"
timeout_s: 5.0
state: connected
```

Required keys:

- `alias`;
- `resource`;
- `connected`;
- `communication_ok`;
- `transport`;
- `identity`;
- `timeout_s`;
- `state`.

Allowed `state` values:

```text
disconnected
connecting
connected
degraded
recovering
faulted
```

This is the public, lowercase projection of the canonical session-state model that RFDS-003 §13.1 owns; RFDS-003 is authoritative for the complete internal state set. Implementers exposing the public `state` field shall map RFDS-003's internal states onto this reduced public vocabulary rather than inventing separate state names.

### 12.2 File-transfer result schema

```yaml
operation: upload
source_path: ./calibration/ch1.csv
destination_path: /calibration/ch1.csv
bytes_transferred: 4096
overwritten: false
verified: true
```

### 12.3 Safe-shutdown result schema

```yaml
safe: true
actions:
  - action: disable_output
    target: channel_1
    result: pass
  - action: open_relays
    target: all
    result: pass
failed_actions: []
confirmed_at: "2026-07-26T08:35:00+03:00"
```

---

## 13. Connection and state semantics

### 13.1 Constructor behavior

The library constructor may:

- store configuration defaults;
- validate static configuration;
- initialize local data structures;
- create locks that do not interact with hardware.

The constructor shall not:

- open a device connection;
- send protocol commands;
- enable outputs;
- reset hardware;
- start non-daemon worker activity;
- require that hardware is present merely to import the library.

### 13.2 Explicit state preconditions

Each device-facing keyword shall define its required state.

Typical states include:

```text
disconnected
connected
configured
ready
running
faulted
```

A keyword called in the wrong state shall fail with `DriverStateError` before unsafe transmission where possible.

### 13.3 Idempotency

The following shall be idempotent:

- `Disconnect`;
- `Disconnect All`;
- `Disable Output`;
- `Open Relay` when already open;
- `Close Relay` when already closed;
- `Safe Shutdown`;
- clearing an already empty local driver error state.

Other keyword idempotency shall be documented.

### 13.4 Cached versus live data

Keywords returning cached state shall say so explicitly.

Where both are useful, the keyword shall provide a `refresh` argument or separate clearly named operation. A cached value shall not be presented as a confirmed live device value.

---

## 14. Timeout, wait, and retry standard

### 14.1 Bounded execution

Every device-facing keyword shall have bounded execution.

A keyword shall not:

- wait forever for a response;
- poll indefinitely;
- block forever on a worker thread;
- retry without a finite attempt count or deadline.

### 14.2 Timeout units

Public timeout arguments shall use seconds and the `_s` suffix.

Timeout values shall be positive finite numbers.

### 14.3 Stabilization waits

A stabilization delay shall be separate from communication timeout when both concepts apply.

Preferred argument names:

```text
stabilization_s
settle_timeout_s
poll_interval_s
```

### 14.4 Retries

Retries shall be used only for documented transient failures.

The driver shall document:

- retryable error classes;
- maximum attempts;
- delay or backoff;
- total time bound;
- whether the command may be repeated safely;
- whether recovery changes device state.

A non-idempotent command shall not be retried automatically unless the protocol provides evidence that it was not applied.

---

## 15. Error and exception standard

### 15.1 Mandatory exception hierarchy

RFDS-007 is the sole normative source for the exact RFDS exception hierarchy, class names, and error codes. Every RFDS Python driver shall expose or internally use the RFDS-007 hierarchy, rooted at `DriverError`, with top-level categories for configuration, validation, state, connection, transport (including timeouts), protocol, device, resource, safety, dependency, and internal failures.

RFDS-002 does not restate the full hierarchy here; see RFDS-007 §6 for the complete, authoritative class tree. A package may add subclasses but shall preserve the RFDS-007 semantic categories and shall not introduce a competing top-level taxonomy.

### 15.2 Error messages

Expected driver failures shall use the stable diagnostic message format defined normatively by RFDS-007 §11:

```text
[<ERROR_CODE>] <operation> failed: <reason>. <context>. Retryable=<yes|no>. Recovery=<action|none>.
```

Where `<ERROR_CODE>` follows the RFDS-007 code grammar `RFDS-<DOMAIN>-<NNN>`. Example:

```text
[RFDS-TMO-001] Get Identity failed: no response within 5.0 s. keyword=Get Identity; alias=default. Retryable=yes. Recovery=Check cable and retry Connect.
```

RFDS-007 is authoritative for the exact message grammar and error-code catalogue; RFDS-002 constrains only which contextual fields (keyword, alias) a device-facing failure shall include.

Mandatory rules:

- failure summaries shall be understandable without reading source code;
- the driver shall not expose passwords, access tokens, or private keys;
- raw binary data shall be bounded in length;
- the original exception shall be chained in Python when useful;
- protocol/device failures shall not be reported as success values;
- validation failures shall identify the argument and accepted range or values;
- errors shall distinguish local validation, driver state, transport, protocol, device, and safety causes.

### 15.3 Robot Framework assertion keywords

Keywords ending in `Should` or containing `Should Be` shall:

- return `None` on success;
- raise an assertion-style failure on mismatch;
- include actual and expected values;
- avoid changing device state unless the assertion explicitly requires a safe probe.

### 15.4 Recovery information

Recoverable errors should include a concrete recovery action.

RFDS-017 shall declare whether each expected error is:

- retryable;
- reconnect-required;
- reset-required;
- operator-action-required;
- non-recoverable within the current test.

---

## 16. Safety standard

### 16.1 Risk classification

Every device-facing public keyword shall declare one risk level:

```text
low
medium
high
critical
```

Recommended interpretation:

- `low` — read-only or benign local operation;
- `medium` — state change within normal safe limits;
- `high` — output, load, motion, heating, switching, reset, deletion, or raw protocol operation;
- `critical` — operation capable of immediate equipment damage, unsafe energy, irreversible loss, or fixture hazard without validated preconditions.

This four-level, lowercase `low`/`medium`/`high`/`critical` scale is the canonical RFDS risk-level vocabulary. RFDS-013 and RFDS-014 shall reuse these exact values (adding `none` only where a capability or field genuinely carries no risk) rather than introducing separately-cased or separately-named risk scales.

### 16.2 Safety validation

High- and critical-risk keywords shall:

- validate connection and device state;
- validate configured limits;
- validate channel and range;
- reject non-finite numeric values;
- document side effects;
- define cleanup or safe-state behavior;
- be included in the RFDS-017 safety rules;
- be constrained by RFDS-018 bench rules when used in a multi-instrument bench.

### 16.3 Dangerous defaults

A default argument shall not:

- enable an output;
- select maximum voltage, current, load, temperature, or power;
- overwrite a device file;
- clear calibration;
- reset a device;
- bypass interlocks;
- activate raw I/O;
- disable error checks.

### 16.4 Emergency cleanup

A driver with persistent hazardous state shall provide `Safe Shutdown` and document the exact teardown sequence.

Failure to confirm a safe state shall be visible as a test failure and shall not be reduced to a warning.

---

## 17. Logging and evidence

Public keywords shall produce useful Robot Framework logs without exposing secrets or overwhelming the report.

### 17.1 Required logging

For device-facing keywords, logs should include:

- canonical keyword name;
- selected alias and redacted resource;
- normalized arguments;
- operation duration;
- retry count;
- result summary;
- protocol trace reference when conformance tracing is enabled.

### 17.2 Protocol logging

Normal user logs should not expose unlimited raw protocol traffic.

Detailed TX/RX data may be emitted at debug or trace level and shall:

- be length-bounded;
- be timestamped;
- distinguish transmitted and received data;
- identify the keyword and protocol vector;
- redact credentials;
- preserve raw bytes in a deterministic representation when required by RFDS-019.

---

## 18. Keyword tags and metadata

Each public keyword shall declare relevant stable tags.

Required tag vocabulary:

```text
rfds:connection
rfds:identity
rfds:query
rfds:measurement
rfds:configuration
rfds:write
rfds:output
rfds:relay
rfds:file
rfds:diagnostic
rfds:assertion
rfds:safety
rfds:destructive
rfds:raw_io
rfds:deprecated
rfds:low_risk
rfds:medium_risk
rfds:high_risk
rfds:critical_risk
```

At minimum, each device-facing keyword shall have:

- one functional classification tag;
- one risk tag.

Tags are metadata and shall not replace documentation or RFDS-017 capability definitions.

---

## 19. Keyword documentation standard

Every public keyword shall document:

1. purpose;
2. canonical signature;
3. each argument and unit;
4. accepted values and ranges;
5. defaults;
6. return type and schema;
7. connection and state preconditions;
8. postconditions;
9. device side effects;
10. risk level;
11. communication timeout behavior;
12. stabilization or readiness wait;
13. retry behavior;
14. expected exception categories;
15. cleanup requirements;
16. aliases and deprecation status;
17. one minimal Robot Framework example.

The first documentation paragraph shall be a concise operation summary suitable for Libdoc and Robot Framework logs.

Documentation shall distinguish:

- setpoint from measured value;
- cached from live value;
- command from query;
- device error from transport error;
- safe operation from potentially hazardous operation.

---

## 20. Assertions versus action keywords

Driver libraries may provide domain-specific assertions when they improve readability or add device-aware tolerance and error handling.

Examples:

```robotframework
Device Should Be Connected
Output Should Be Disabled    channel=1
Voltage Should Be Within Limits    channel=1
Device Error Queue Should Be Empty
Relay Should Be Open    channel=3
```

Rules:

- assertion keywords shall not duplicate generic BuiltIn assertions without adding domain value;
- action keywords shall not silently assert unrelated conditions after completing the requested action;
- verification that is required for safety may remain part of the action keyword and shall be documented;
- assertion tolerances and units shall be explicit.

---

## 21. Aliases, compatibility, and deprecation

### 21.1 Canonical names

Each operation shall have exactly one canonical keyword name.

Aliases may exist for:

- migration from a previous driver API;
- vendor terminology;
- compatibility with an established project interface;
- corrected spelling or naming.

Aliases shall not be used to create multiple competing canonical styles.

### 21.2 Alias equivalence

An alias shall:

- call the same implementation path as the canonical keyword;
- accept equivalent arguments unless a documented migration adapter is required;
- return the same type and semantic value;
- produce equivalent device protocol behavior;
- be listed separately in the public API inventory and RFDS-019 coverage matrix.

### 21.3 Deprecation

A deprecated keyword shall:

- remain callable during the deprecation window;
- emit a Robot Framework deprecation warning;
- identify the replacement keyword;
- appear in Libdoc, README migration notes, history, and the AI Driver Contract;
- carry the `rfds:deprecated` tag;
- remain covered by RFDS-019 until removed.

Recommended documentation prefix:

```text
*DEPRECATED* Use `Connect` instead. Scheduled for removal after v26.04.
```

### 21.4 Minimum deprecation window

A public keyword, argument, return key, or behavior shall remain deprecated for at least two subsequent released driver revisions before removal.

A shorter window is permitted only for:

- a safety defect;
- a security defect;
- an operation that cannot work correctly;
- accidental exposure of a private implementation method.

The reason shall be documented in `history/` and `review/`.

### 21.5 Breaking changes

The following are breaking API changes:

- removing a canonical keyword or alias;
- renaming a keyword without retaining an alias;
- changing argument order;
- removing an argument;
- changing a default with behavioral impact;
- changing a return type;
- removing or renaming a return dictionary key;
- changing units;
- changing Boolean meaning;
- changing output or safety side effects;
- changing protocol behavior in a way visible to the public contract.

Breaking changes require explicit release notes, migration guidance, contract updates, and conformance updates.

---

## 22. Mandatory API artifacts

Every driver package shall include equivalent artifacts:

```text
rf_<driver_name>/
├── api/
│   ├── public_api.yaml
│   ├── public_api.schema.json
│   └── compatibility.yaml
├── docs/
│   ├── keyword_reference.md
│   └── keyword_reference.html
├── ai/
│   ├── ai_contract.yaml
│   └── ai_contract.lock
├── tests/
│   ├── api/
│   │   ├── mandatory_api.robot
│   │   ├── naming_and_signature.robot
│   │   ├── return_type.robot
│   │   └── compatibility.robot
│   └── conformance/
│       └── ...
├── history/
│   └── ...
└── review/
    └── ...
```

Generated Libdoc HTML may be published through GitHub Pages.

---

## 23. `public_api.yaml` minimum schema

Each public keyword entry shall contain at least:

```yaml
api_spec:
  id: RFDS-002
  version: "1.0"

library:
  name: rf_example
  version: "26.01"
  scope: SUITE

keywords:
  - name: Connect
    canonical_name: Connect
    python_method: connect
    aliases: []
    category: connection
    capability_id: connection
    device_facing: true
    risk: low
    arguments:
      - name: resource
        type: str | None
        required: false
        default: null
      - name: alias
        type: str
        required: false
        default: default
      - name: timeout_s
        type: float | None
        required: false
        default: null
      - name: options
        type: dict
        required: false
        default: {}
    returns:
      type: dict
      schema: connection_state
    preconditions: []
    postconditions:
      - requested alias is connected
    side_effects:
      - opens transport session
    timeout_behavior: bounded
    protocol_vector: connect.default
    tags:
      - rfds:connection
      - rfds:low_risk
    status: active
    deprecated_since: null
    replacement: null
```

The schema shall remain synchronized with Libdoc, RFDS-017, examples, and RFDS-019 keyword inventory.

---

## 24. Implementation skeleton

A compliant static Python library may use this pattern:

```python
from __future__ import annotations

from typing import Any

from robot.api.deco import keyword, library

from .errors import DriverStateError
from .version import __version__


@library(scope="SUITE", version=__version__, auto_keywords=False)
class ExampleDriverLibrary:
    """Robot Framework library for the Example device family."""

    def __init__(self, default_timeout_s: float = 5.0) -> None:
        self._default_timeout_s = self._validate_timeout(default_timeout_s)
        self._sessions: dict[str, Any] = {}
        self._active_alias: str | None = None

    @keyword("Connect", tags=["rfds:connection", "rfds:low_risk"])
    def connect(
        self,
        resource: str | None = None,
        alias: str = "default",
        timeout_s: float | None = None,
        **options: Any,
    ) -> dict[str, Any]:
        """Establish a device session and return normalized connection state."""
        ...

    @keyword("Disconnect", tags=["rfds:connection", "rfds:low_risk"])
    def disconnect(self, alias: str | None = None) -> None:
        """Close a device session. Safe to call more than once."""
        ...

    @keyword("Is Connected", tags=["rfds:query", "rfds:low_risk"])
    def is_connected(self, alias: str | None = None) -> bool:
        """Return whether the selected session is currently connected."""
        ...

    @keyword("Get Identity", tags=["rfds:identity", "rfds:low_risk"])
    def get_identity(self, alias: str | None = None, refresh: bool = True) -> str:
        """Return the device identity string."""
        ...

    def _require_session(self, alias: str | None) -> Any:
        """Internal helper. Not a Robot Framework keyword."""
        ...

    @staticmethod
    def _validate_timeout(value: float) -> float:
        ...
```

---

## 25. Robot Framework usage example

```robotframework
*** Settings ***
Library    rf_example.ExampleDriverLibrary
Suite Teardown    Safe Driver Teardown

*** Test Cases ***
Read Device Identity
    ${state}=    Connect
    ...    resource=TCPIP0::192.168.0.55::5025::SOCKET
    ...    alias=psu
    ...    timeout_s=5.0
    Should Be True    ${state}[connected]

    ${ok}=    Check Communication    alias=psu
    Should Be True    ${ok}

    ${identity}=    Get Identity    alias=psu
    Should Not Be Empty    ${identity}

*** Keywords ***
Safe Driver Teardown
    Run Keyword And Ignore Error    Safe Shutdown    alias=psu
    Disconnect    alias=psu
```

A driver that does not declare `safe_shutdown` shall omit that teardown step and use `Disconnect` only.

---

## 26. Mandatory API tests

Each driver shall provide automated tests that verify:

1. the library imports without hardware access;
2. automatic keyword discovery is disabled;
3. all expected canonical keywords are exported;
4. no private helper is exported;
5. normalized keyword names are unique;
6. mandatory universal signatures match this specification or an approved compatibility profile;
7. all arguments and return values are documented;
8. public methods have type annotations;
9. command and query return types match the API inventory;
10. invalid local arguments fail before transmission where practical;
11. `Disconnect` is idempotent;
12. `Is Connected` returns a Boolean;
13. `Get Driver Information` and `Get Driver Capabilities` match package metadata;
14. aliases are semantically equivalent;
15. deprecated keywords emit warnings;
16. all device-facing keywords are linked to RFDS-019 protocol vectors or approved exclusions.

---

## 27. Integration with other RFDS specifications

### 27.1 RFDS-017 — AI Driver Contract

RFDS-017 shall use RFDS-002 as the source of truth for:

- canonical keyword name;
- alias list;
- signature;
- argument types and units;
- return type and schema;
- preconditions and postconditions;
- side effects;
- risk level;
- timing, timeout, and retry behavior;
- errors and recovery;
- resource use.

Every public keyword in RFDS-002 inventory shall have one corresponding RFDS-017 capability entry or an explicitly documented metadata-only classification.

### 27.2 RFDS-018 — AI Test Bench Contract

RFDS-018 shall reference RFDS-002 canonical keyword names when defining:

- driver ordering;
- shared resource use;
- setup and teardown;
- safe-state operations;
- multi-driver workflows;
- conflict and scheduling rules.

### 27.3 RFDS-019 — Driver Call and Protocol Conformance

RFDS-019 shall verify:

- the exported keyword inventory;
- canonical and alias names;
- signatures and defaults;
- callability through Robot Framework;
- return types;
- outbound protocol behavior;
- inbound parsing;
- error behavior;
- alias equivalence.

A public API change is incomplete until corresponding RFDS-019 inventory, vectors, tests, and evidence are updated.

### 27.4 Driver implementation lifecycle

Each lifecycle gate that changes public behavior shall update:

- implementation;
- `public_api.yaml`;
- Libdoc and keyword reference;
- RFDS-017 contract;
- RFDS-019 inventory and protocol vectors;
- examples;
- `history/` change record;
- `review/` API review.

---

## 28. Conformance levels

### Level 0 — Declaration

- library version and scope declared;
- automatic keyword discovery disabled;
- public API inventory exists;
- mandatory universal keywords declared.

### Level 1 — Naming and signature

- canonical names follow this standard;
- normalized names are unique;
- signatures, defaults, types, and units comply;
- aliases and deprecations are declared.

### Level 2 — Runtime callability

- each supported public keyword is callable through Robot Framework;
- valid arguments convert correctly;
- return values are Robot Framework-compatible;
- expected failures use the required exception categories.

### Level 3 — Semantic behavior

- connection and state behavior matches this specification;
- idempotency requirements pass;
- timeouts are bounded;
- safety and cleanup behavior are confirmed;
- return schemas remain stable.

### Level 4 — Protocol traceability

- every device-facing keyword is linked to RFDS-019 protocol evidence;
- aliases exhibit equivalent protocol behavior;
- failures and recovery are traceable.

---

## 29. Acceptance criteria

A driver passes RFDS-002 only when:

1. automatic keyword discovery is disabled;
2. 100% of exported keywords are explicitly declared in the public API inventory;
3. no private or unintended method is exported;
4. all mandatory universal keywords are implemented;
5. every declared conditional capability contains its mandatory keyword group;
6. canonical keyword names follow the naming rules;
7. keyword names are unique after Robot Framework normalization;
8. all public signatures, defaults, types, units, return types, and dictionary schemas are documented;
9. all public Python methods are type-annotated;
10. all public returns are Robot Framework-compatible;
11. constructor and import operations do not access hardware;
12. connection, timeout, state, and idempotency semantics pass automated tests;
13. dangerous operations have explicit risk and safety metadata;
14. aliases and deprecated keywords follow compatibility rules;
15. `public_api.yaml`, Libdoc, RFDS-017, and RFDS-019 are mutually consistent;
16. every device-facing public keyword has RFDS-019 protocol coverage or approved exclusion;
17. no mandatory API test remains `NOT RUN`.

---

## 30. Failure conditions

RFDS-002 shall fail when:

- a helper method is exported accidentally;
- a public keyword is missing from the inventory;
- a mandatory universal keyword is absent;
- a declared capability omits a mandatory capability keyword;
- two keywords collide after normalization;
- a keyword has ambiguous action semantics;
- a signature changes without compatibility handling;
- units are ambiguous;
- a command returns an undocumented or non-serializable object;
- a query returns a formatted string instead of the documented numeric type;
- a Boolean state uses inconsistent meaning;
- a connection is opened during import or construction;
- a keyword can block indefinitely;
- invalid local data is transmitted when it could have been rejected safely;
- a dangerous default enables or overwrites something;
- expected driver errors are reported as success;
- an alias differs from its canonical operation without documentation;
- a deprecated keyword is removed before the required window;
- API metadata and runtime Libdoc disagree;
- a device-facing keyword lacks RFDS-019 coverage and approved exclusion.

---

## 31. API review checklist

1. Is automatic keyword discovery disabled?
2. Are all public keywords explicitly decorated or registered?
3. Are all canonical names verb-first and unambiguous?
4. Are normalized names unique?
5. Are all universal keywords implemented?
6. Are capability declarations accurate?
7. Does each capability include its mandatory keyword group?
8. Are connection semantics explicit and idempotent where required?
9. Does the constructor avoid hardware access?
10. Are arguments named consistently and units explicit?
11. Are defaults deterministic and safe?
12. Are all arguments and returns type-annotated?
13. Are return values Robot Framework-compatible?
14. Are dictionary keys stable and documented?
15. Are timeout, stabilization, polling, and retries bounded?
16. Are error categories and recovery actions clear?
17. Are high-risk operations classified and constrained?
18. Is safe shutdown provided where persistent hazardous state is possible?
19. Are aliases equivalent and deprecations visible?
20. Do Libdoc, `public_api.yaml`, RFDS-017, examples, and RFDS-019 agree?
21. Is every device-facing keyword covered by a protocol vector or exclusion?
22. Are API changes recorded in `history/` and reviewed in `review/`?

---

## 32. Minimum definition of done

RFDS-002 implementation for a driver is complete when:

- the mandatory universal API is implemented;
- all applicable capability groups are implemented;
- the public keyword inventory is complete;
- Libdoc and machine-readable API documentation are generated;
- API tests pass;
- the AI Driver Contract is synchronized;
- call and protocol conformance data are synchronized;
- examples use only canonical keywords unless demonstrating migration;
- compatibility and deprecation records are current;
- API review finds no unresolved Critical or Major issue.

---

## 33. Goal

Provide one predictable, safe, machine-verifiable public interface across all RFDS Robot Framework hardware drivers while preserving the device-specific capabilities necessary for real laboratory automation.

---

## Appendix A — Canonical mandatory keyword summary

### Universal keywords

| Keyword | Return | Required for every driver |
|---|---:|---:|
| `Connect` | `dict` | Yes |
| `Disconnect` | `None` | Yes |
| `Is Connected` | `bool` | Yes |
| `Get Connection State` | `dict` | Yes |
| `Check Communication` | `bool` | Yes |
| `Get Identity` | `str` | Yes |
| `Get Driver Information` | `dict` | Yes |
| `Get Driver Capabilities` | `list[str]` | Yes |
| `Set Communication Timeout` | `float` | Yes |
| `Get Communication Timeout` | `float` | Yes |

### Common conditional groups

| Capability | Mandatory canonical keywords |
|---|---|
| Multi-connection | `List Connections`, `Select Connection`, `Disconnect All`, `Get Active Connection` |
| Error queue | `Get Device Error`, `Get All Device Errors`, `Clear Device Errors`, `Device Error Queue Should Be Empty` |
| Channel selection | `List Channels`, `Validate Channel` |
| Output control | `Enable Output`, `Disable Output`, `Get Output State`, output-state assertions |
| Measurement | `Measure <Quantity>` |
| Source/setpoint | `Set <Quantity>`, `Get <Quantity> Setpoint`, `Get <Quantity> Limits` |
| Relay control | open, close, set, get, all-open, all-state, and assertion keywords |
| Reset | `Reset Device` |
| File transfer | list, upload, download, and delete file keywords |
| Safe shutdown | `Safe Shutdown` |
| Raw I/O | raw write, query, and read keywords with explicit opt-in |

---

## Appendix B — Recommended canonical migration aliases

Legacy driver packages may temporarily map earlier names to RFDS-002 canonical names:

| Legacy pattern | Canonical replacement |
|---|---|
| `Open`, `Open Connection`, `Connect To Device`, `Connect DMM`, `Connect Relays` | `Connect` |
| `Close`, `Close Connection`, `Close DMM`, `Disconnect Relays` | `Disconnect` |
| `Get IDN`, `Query Identity`, `Read Identity` | `Get Identity` |
| `Set Timeout` | `Set Communication Timeout` |
| `Get Timeout` | `Get Communication Timeout` |
| `Close All Relays` when meaning electrically close | Keep `Close All Relays`; do not map to `Disconnect All` |
| `Open All Relays` when meaning electrically open | Keep `Open All Relays`; do not map to `Disconnect All` |

Migration aliases shall be deprecated, tested, and removed only through the change-control process.

---

## Appendix C — Source basis

This specification is designed to align with:

- RFDS-017 — AI Driver Contract Specification;
- RFDS-018 — AI Test Bench Contract Specification;
- RFDS-019 — Robot Framework Driver Call and Protocol Conformance Test Specification;
- RFDS-020 — Driver Implementation Lifecycle;
- Robot Framework User Guide sections covering test library APIs, keyword discovery, keyword names, type conversion, library scope, Libdoc, and keyword deprecation.
