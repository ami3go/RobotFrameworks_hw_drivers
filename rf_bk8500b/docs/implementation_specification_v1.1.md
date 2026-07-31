# AI-Agent Software Development Specification
## Production-Grade Python Driver for B&K Precision 8500B Series DC Electronic Loads

**Document version:** 1.1  
**Date:** 2026-07-13  
**Status:** Approved implementation specification; hardware-validation gates remain mandatory for stable legacy support and production designation  
**Target service profile:** Continuous laboratory and industrial test operation, 24 hours/day, 7 days/week  
**Primary implementation language:** Python 3  
**Package layout:** Python package at repository root; do not use a `src/` directory

---

## 1. Purpose

**[SCOPE-001]** This document is the authoritative implementation task for an AI coding agent that must design, implement, test, document, and package a production-grade Python driver for the B&K Precision 8500B Series programmable DC electronic loads.

**[SCOPE-002]** The driver shall support dependable unattended operation in automated test equipment, production test, burn-in, validation, and laboratory systems. It shall prioritize deterministic behavior, electrical safety, bounded failure modes, protocol correctness, testability, observability, and maintainability over minimal code size or rapid prototyping.

**[SCOPE-003]** The result shall be a complete installable Python project, not a demonstration script.

### 1.1 Normative language and requirement identifiers

**[SCOPE-004]** The words **shall**, **shall not**, **must**, **must not**, **required**, and **prohibited** are normative. The words **should**, **recommended**, **may**, and **optional** are informative unless a release gate explicitly promotes them to mandatory status.

**[SCOPE-005]** Every normative paragraph or list requirement in this document shall carry a stable identifier in the form `CATEGORY-NNN`. A single identifier may cover multiple inseparable clauses in the same paragraph. Child bullets inherit the identifier of their tagged parent unless they have their own identifier.

Narrative requirements use the visible inline identifiers in this document. Exact API signatures, command-policy rows, tables, and gate checklists use deterministic structural identifiers in the generated traceability document, for example `API-S9.7-set_current_setpoint`, `CMD-SCPI-INP-SET`, `G0-DEL-001`, and `G0-EXIT-001`. These structural identifiers are normative and shall remain stable after Gate G0.

Required identifier categories are:

| Prefix | Scope |
|---|---|
| `SCOPE` | Product scope and source authority |
| `MODEL` | Models, interfaces, and capabilities |
| `ARCH` | Architecture, ownership, and concurrency |
| `CFG` | Configuration and validation |
| `API` | Frozen public API and compatibility |
| `PROTO-SCPI` | SCPI protocol behavior |
| `PROTO-LEG` | Legacy binary protocol behavior |
| `EXEC` | Command execution, deadlines, retry, and state machines |
| `SAFE` | Electrical and operational safety |
| `OBS` | Logging, audit, metrics, and diagnostics |
| `TEST` | Automated test requirements |
| `HIL` | Hardware-in-the-loop requirements |
| `REL` | Endurance, packaging, and release criteria |
| `AGENT` | AI-agent implementation and deviation controls |

**[SCOPE-006]** `docs/requirements_traceability.md` shall map every requirement identifier to source-manual references, implementation owner, unit/integration/HIL tests, evidence artifacts, and release-gate status. A requirement without an implementation owner and verification method is incomplete and shall block the gate that first depends on it.

---

## 2. Source material and authority

### 2.1 Primary source

The supplied programming-manual conversion is the initial command and protocol source:

- File: `8500B_Series_programming_manual.md`
- Stated source-manual version date: 2019-07-23
- SHA-256: `c169a171da1ea82b17c20045980bb0fa165297ccb3d8c20e10141389f7b07f79`

### 2.2 Supplemental authoritative sources

The agent may use only authoritative manufacturer or project documentation to resolve implementation details:

1. B&K Precision official 8500B Series product documentation.
2. The original manufacturer PDF corresponding to the supplied Markdown conversion.
3. B&K Precision official remote-communication guidance.
4. Official pySerial documentation.
5. Official PyVISA documentation, only if the optional VISA adapter is implemented.
6. Hardware traces captured from real 8500B-series instruments.

### 2.3 Conflict-resolution order

When sources disagree, use this order:

1. Reproducible behavior observed on supported hardware and documented in a hardware-validation record.
2. Current official B&K Precision programming manual PDF.
3. Current official B&K Precision product/user documentation.
4. Supplied Markdown manual conversion.
5. Explicitly documented engineering assumption.

**[SCOPE-007]** The agent shall never silently choose between conflicting values. Every conflict shall be recorded in `docs/protocol_assumptions.md`, including source, selected behavior, test evidence, and affected models/firmware.

---

## 3. Supported instruments and interfaces

### 3.1 Required model family

**[MODEL-001]** The stable driver shall support these single-channel 8500B Series models:

| Model | Maximum voltage | Maximum current | Maximum power | Physical PC interface |
|---|---:|---:|---:|---|
| 8500B | 150 V | 30 A | 300 W | TTL DB9 through supported adapter |
| 8502B | 500 V | 15 A | 300 W | TTL DB9 through supported adapter |
| 8510B | 120 V | 120 A | 600 W | TTL DB9 through supported adapter |
| 8514B | 120 V | 240 A | 1500 W | USB and RS-232 |
| 8542B | 150 V | 30 A | 150 W | TTL DB9 through supported adapter |

**[MODEL-002]** Runtime ratings reported by the instrument shall take precedence over this table. The table is a conservative fallback for identification and pre-validation only.

### 3.2 Physical-interface safety

**[MODEL-003]** For models with TTL-level DB9 communication, the documentation shall clearly state that a conventional RS-232 cable or generic RS-232-to-USB adapter shall not be connected directly. The supported B&K/ITECH-compatible TTL adapter shall be used.

**[MODEL-004]** The default serial configuration shall be configurable and shall initially use the manufacturer-supported values below, subject to hardware validation:

- Baud rate: 9600 baud by default.
- Data bits: 8, provisional until verified against the original manual/hardware.
- Parity: none.
- Stop bits: 1, provisional until verified.
- DTR asserted.
- RTS asserted.
- Hardware flow control disabled unless a validated interface specifically requires it.
- Instrument communication address: 0 by default.
- Instrument connection mode: `separate`, configured from the front panel when required.

### 3.3 Supported transport implementations

Required:

- `SerialTransport` based on pySerial, supporting Windows and Linux.
- User-injected transport interface for test doubles and custom integrations.

Optional but recommended:

- `VisaSerialTransport` based on PyVISA for users already operating a VISA stack.

**[MODEL-005]** The stable public API shall not depend on PyVISA. PyVISA support, if implemented, shall be an optional package extra.

### 3.4 Explicitly out of scope

**[MODEL-006]** The following are not required unless a later manufacturer document is supplied:

- Ethernet/LXI communication.
- GPIB communication.
- Firmware update.
- Internal calibration writes.
- Multi-channel operation; the listed 8500B models are single-channel instruments.
- GUI application.
- Automatic control of external power supplies or relays.

---

## 4. Protocol strategy

### 4.1 Required protocol families

**[PROTO-SCPI-001]** The driver shall implement both documented protocol families behind a shared high-level API:

1. **SCPI ASCII protocol** for common commands, status, measurements, fixed modes, dynamic mode, LED simulation, OCP testing, peak capture, timing, and system functions.
2. **Legacy 26-byte binary frame protocol** for backwards compatibility and advanced features not represented in the supplied SCPI command set, including list, battery/autotest-related, protection, trigger, timer, and detailed rating/status functions.

### 4.2 Protocol selection

**[PROTO-SCPI-002]** Public configuration shall support:

- `protocol="scpi"` — default stable choice.
- `protocol="legacy"` — explicit binary protocol.
- `protocol="auto"` — opt-in only; uses read-only probes and records the detected protocol.

**[PROTO-SCPI-003]** The driver shall not alternate SCPI and legacy frames within an active session unless hardware validation proves that the selected instrument/firmware safely supports such switching. A protocol switch shall otherwise require closing and reopening the session.

### 4.3 Auto-detection safety

**[PROTO-SCPI-004]** Protocol auto-detection shall:

1. Open the port with finite timeouts.
2. Clear only host-side input buffers.
3. Probe SCPI using harmless identity/version queries and candidate terminators.
4. Close and reopen the transport before a legacy probe.
5. Probe legacy using a read-only information command.
6. Never enable the load input, short circuit, recall state, reset, clear protection, or modify a limit.
7. Return a detailed detection report when no protocol is verified.

---

## 5. Product goals and quality attributes

### 5.1 Functional goal

Expose a typed, documented Python API for the full stable command set supported by the instrument, with protocol-specific capability checks and consistent SI-unit values.

### 5.2 24/7 reliability goal

**[REL-001]** Under a stable physical connection, the driver shall support continuous operation without unbounded memory growth, descriptor leaks, deadlocks, orphaned worker threads, stale-buffer accumulation, or permanent session corruption after recoverable I/O faults.

### 5.3 Safety goal

**[REL-002]** The driver shall never turn the electronic-load input on implicitly during construction, connection, identity detection, reconnection, protocol probing, cleanup, or state synchronization.

### 5.4 Determinism goal

**[REL-003]** All communication calls shall have bounded timeouts. There shall be at most one in-flight request per physical session. Unit conversion, quantization, retry behavior, and exception mapping shall be deterministic.

### 5.5 Maintainability goal

**[REL-004]** Protocol codecs, transport I/O, device semantics, safety policy, and public API shall be separated so that a new transport or firmware quirk can be added without rewriting the driver.

---

## 6. Repository and package structure

**[ARCH-001]** The repository shall use a root package layout and shall not contain a `src/` directory.

```text
bk8500b-driver/
├── pyproject.toml
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── bk8500b/
│   ├── __init__.py
│   ├── device.py
│   ├── async_device.py
│   ├── execution.py
│   ├── state_machine.py
│   ├── config.py
│   ├── capabilities.py
│   ├── enums.py
│   ├── exceptions.py
│   ├── measurements.py
│   ├── safety.py
│   ├── status.py
│   ├── diagnostics.py
│   ├── cli.py
│   ├── transport/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── serial.py
│   │   └── visa.py
│   ├── protocol/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── scpi.py
│   │   ├── legacy.py
│   │   ├── legacy_codec.py
│   │   ├── scaling.py
│   │   └── command_catalog.py
│   └── experimental/
│       ├── __init__.py
│       ├── battery.py
│       └── autotest.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── property/
│   ├── fault_injection/
│   └── hardware/
├── examples/
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── command_coverage.md
│   ├── protocol_assumptions.md
│   ├── safety.md
│   ├── long_running_operation.md
│   ├── troubleshooting.md
│   ├── hardware_validation.md
│   └── release_checklist.md
└── tools/
```

The package/module names shown above are frozen for v1.0 implementation. Renaming, merging, or removing them requires an approved Architecture Decision Record (ADR), updated traceability, and migration notes. The root package layout is mandatory.

---

## 7. Architectural requirements

### 7.1 Layering

**[ARCH-002]** The implementation shall contain these logical layers:

1. **Transport layer** — byte transport, open/close, finite reads/writes, buffer control, serial configuration.
2. **Protocol layer** — SCPI and legacy message encoding/decoding, framing, checksums, parsing, command timing.
3. **Execution layer** — serialized command execution, deadlines, retry classification, reconnection, tracing.
4. **Capability layer** — model, firmware, protocol, limits, and feature availability.
5. **Device-semantic layer** — modes, setpoints, measurement, protection, status, tests, list/battery operations.
6. **Safety-policy layer** — preconditions and guarded enable/short/high-risk operations.
7. **Public API layer** — stable typed synchronous API and asynchronous facade.

### 7.2 No global mutable session state

**[ARCH-003]** No open serial port, active device, command buffer, retry counter, or safety state shall be stored in global mutable variables.

### 7.3 Single request owner

**[ARCH-004]** One lock shall serialize every request/response transaction on a session. Calls from multiple threads may be accepted, but I/O shall never interleave.

### 7.4 Multiprocess behavior

**[ARCH-005]** The driver shall document that one physical serial port shall have one owning process. It shall request exclusive port access where the operating system and pySerial support it. Port ownership failures shall produce a clear exception.

### 7.5 Public synchronous core

**[ARCH-006]** The synchronous class is the canonical implementation. The asynchronous class shall delegate to the same synchronous command engine through a dedicated serialized worker and shall not duplicate protocol logic.

### 7.6 Dependency policy

**[ARCH-007]** Runtime dependencies shall be minimal. The only mandatory third-party runtime dependency for the stable serial implementation shall be `pyserial`. Any additional runtime dependency requires an ADR explaining why the standard library or existing dependency is insufficient. PyVISA, documentation, test, lint, type-check, and property-test dependencies shall remain optional extras or development dependencies.

### 7.7 Formal runtime state machines

**[ARCH-008]** The implementation shall encode the following states as enums and enforce transitions in one state-machine module. State changes shall be observable through diagnostics and structured logs. Invalid transitions shall raise `InvalidStateTransitionError` and shall not issue instrument I/O.

#### 7.7.1 Session state machine

```text
DISCONNECTED
  -> CONNECTING
  -> IDENTIFYING
  -> CONNECTED_UNSYNCHRONIZED
  -> CONNECTED_READY
  -> DEGRADED
  -> RECONNECTING
  -> CLOSING
  -> DISCONNECTED

Any non-closing state -> FAILED
FAILED -> CLOSING -> DISCONNECTED
```

Rules:

- **[ARCH-009]** Device-control methods are prohibited in `DISCONNECTED`, `CONNECTING`, `IDENTIFYING`, `RECONNECTING`, `CLOSING`, and `FAILED`.
- **[ARCH-010]** Hazardous methods are additionally prohibited in `CONNECTED_UNSYNCHRONIZED` and `DEGRADED`.
- **[ARCH-011]** A successful transport open shall not imply `CONNECTED_READY`; identity, protocol, capability, and state synchronization must complete first.
- **[ARCH-012]** Reconnection shall always enter `CONNECTED_UNSYNCHRONIZED`; cached values shall not promote it to ready.
- **[ARCH-013]** A serial-number mismatch after reconnect shall transition to `FAILED_WRONG_DEVICE`, represented as `FAILED` plus a diagnostic reason.

#### 7.7.2 Command transaction state machine

```text
CREATED -> VALIDATED -> WAITING_FOR_LOCK -> WRITING
WRITING -> WRITE_COMPLETE -> READING -> RESPONSE_VALIDATED -> COMPLETED

CREATED|VALIDATED|WAITING_FOR_LOCK -> CANCELLED_NOT_SENT
WRITING -> FAILED_NOT_SENT | OUTCOME_INDETERMINATE
WRITE_COMPLETE|READING -> RETRYABLE_READ_FAILURE | OUTCOME_INDETERMINATE
RESPONSE_VALIDATED -> COMPLETED | PROTOCOL_FAILURE | DEVICE_REJECTED
```

Rules:

- Only `FAILED_NOT_SENT`, `RETRYABLE_READ_FAILURE` for read-only/idempotent commands, and explicitly catalogued safe failures may be retried automatically.
- **[ARCH-014]** `OUTCOME_INDETERMINATE` shall never be converted to success or ordinary timeout without evidence.
- **[ARCH-015]** Cancellation after writing begins shall produce `IndeterminateCommandOutcome` unless the protocol proves the command was not accepted.
- **[ARCH-016]** Every terminal state shall release the session lock and update metrics exactly once.

#### 7.7.3 Safe-enable state machine

```text
START -> READ_STATE -> FORCE_OR_REQUIRE_OFF -> VALIDATE_ALL
-> APPLY_LIMITS -> APPLY_MODE_AND_SETPOINT -> VERIFY_CONFIGURATION
-> CHECK_PROTECTION -> ENABLE_INPUT -> VERIFY_ENABLED -> COMPLETE
```

**[ARCH-017]** Any failure before `ENABLE_INPUT` shall terminate with input confirmed or presumed OFF. Any failure during or after `ENABLE_INPUT` shall execute a bounded best-effort OFF transaction and return a structured result that states whether OFF was verified, unverified, or impossible to attempt.

#### 7.7.4 Reconnect state machine

```text
DEGRADED -> RECONNECTING -> TRANSPORT_OPEN -> IDENTITY_CHECK
-> PROTOCOL_CHECK -> CAPABILITY_CHECK -> STATE_SYNC
-> CONNECTED_READY | CONNECTED_UNSYNCHRONIZED | FAILED
```

**[ARCH-018]** Automatic replay of input ON, short ON, trigger, reset, recall, protection clear, timer start, OCP start, timing start, or other non-idempotent action is prohibited.

#### 7.7.5 Long-operation state machine

**[ARCH-019]** OCP, timing, self-test, and other long operations shall use:

```text
IDLE -> CONFIGURING -> ARMED -> RUNNING -> COMPLETED
RUNNING -> CANCELLING -> CANCELLED | OUTCOME_INDETERMINATE
Any active state -> FAILED
```

**[ARCH-020]** Each operation shall define its start evidence, completion evidence, cancellation behavior, deadline class, and post-failure synchronization query in the command-policy matrix.

---

## 8. Configuration model

Create an immutable or carefully validated `DriverConfig` containing at least:

- Port/resource name.
- Protocol selection.
- Instrument address.
- Baud rate, parity, data bits, stop bits.
- DTR and RTS states.
- Read, write, query, connect, and long-operation timeouts.
- Minimum inter-command delay.
- Retry policy.
- Reconnect policy.
- SCPI write/read terminators.
- Maximum SCPI response length.
- Maximum error-queue drain count.
- Serial input-buffer size guard where supported.
- `turn_input_off_on_close` policy.
- `restore_configuration_after_reconnect` policy.
- `allow_broadcast_writes` policy.
- Logging/trace configuration.
- Safety policy.

**[CFG-001]** Configuration shall reject impossible and dangerous combinations before opening a port.

No timeout may default to infinite.

---

## 9. Frozen public API contract

**[API-001]** The names and signatures in this section are the required v1.0 public API. Internal implementation details may change, but public names, parameter meaning, return types, exception semantics, and safety behavior shall not change after Gate G3 without an approved compatibility ADR and a major-version plan.

### 9.1 Public exports

**[API-002]** `bk8500b.__init__` shall export exactly these stable symbols for v1.0, excluding documented aliases:

```python
from bk8500b import (
    BK8500B,
    AsyncBK8500B,
    DriverConfig,
    RetryPolicy,
    ReconnectPolicy,
    SafetyPolicy,
    Protocol,
    OperatingMode,
    DynamicMode,
    TriggerSource,
    SessionState,
    CommandOutcome,
    InstrumentIdentity,
    InstrumentCapabilities,
    Measurement,
    MeasurementSnapshot,
    AppliedSetpoint,
    DeviceStatus,
    DiagnosticSnapshot,
    HealthReport,
    SelfTestResult,
    SCPIErrorEntry,
    ProtectionFlag,
    SafetyToken,
    SlewRate,
    TransientConfig,
    LEDConfig,
    OCPTestConfig,
    OCPTestResult,
    TimingTestConfig,
    TimingTestResult,
    ListConfig,
    ListRunResult,
    SafeEnableConfig,
    SafeEnableResult,
)
```

**[API-003]** All exceptions defined in section 17 shall also be public exports. Extension protocols `Transport`, `AuditSink`, and `MetricsSink` shall be imported from `bk8500b.transport` and `bk8500b.diagnostics`; their method contracts shall be frozen in `docs/public_api_contract.md`.

### 9.2 Exact constructor and lifecycle

```python
class BK8500B:
    def __init__(
        self,
        config: DriverConfig,
        *,
        transport: Transport | None = None,
        audit_sink: AuditSink | None = None,
        metrics_sink: MetricsSink | None = None,
    ) -> None: ...

    def connect(self) -> None: ...
    def close(self) -> None: ...
    def reconnect(self) -> None: ...
    def synchronize_state(self) -> DeviceStatus: ...
    def health_check(self) -> HealthReport: ...
    def diagnostic_snapshot(self) -> DiagnosticSnapshot: ...

    @property
    def connected(self) -> bool: ...

    @property
    def session_state(self) -> SessionState: ...

    def __enter__(self) -> "BK8500B": ...
    def __exit__(self, exc_type, exc, tb) -> None: ...
```

**[API-004]** Construction shall validate configuration but shall not open the transport or perform I/O. `connect()` shall be idempotent only when already connected to the same verified device; otherwise it shall raise `InvalidStateTransitionError`.

### 9.3 Exact configuration dataclasses

**[API-005]** The following frozen dataclasses shall be immutable (`frozen=True`) unless runtime mutation is explicitly required:

```python
@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_read_attempts: int = 2
    max_write_attempts: int = 1
    initial_backoff_s: float = 0.05
    maximum_backoff_s: float = 0.5
    jitter_fraction: float = 0.10

@dataclass(frozen=True, slots=True)
class ReconnectPolicy:
    enabled: bool = False
    max_attempts: int = 3
    total_deadline_s: float = 15.0
    require_serial_match: bool = True
    restore_configuration: bool = False

@dataclass(frozen=True, slots=True)
class SafetyPolicy:
    require_off_before_reconfiguration: bool = True
    verify_critical_writes: bool = True
    block_unknown_model_hazards: bool = True
    require_enable_token: bool = False
    turn_input_off_on_close: bool = True
    allow_short: bool = False
    allow_broadcast_writes: bool = False

@dataclass(frozen=True, slots=True)
class DriverConfig:
    port: str
    protocol: Protocol = Protocol.SCPI
    address: int = 0
    baud_rate: int = 9600
    bytesize: int = 8
    parity: str = "N"
    stopbits: float = 1
    dtr: bool = True
    rts: bool = True
    connect_timeout_s: float = 3.0
    read_timeout_s: float = 2.0
    write_timeout_s: float = 2.0
    query_timeout_s: float = 2.0
    long_operation_timeout_s: float = 120.0
    lock_timeout_s: float = 5.0
    close_timeout_s: float = 5.0
    minimum_command_interval_s: float = 0.02
    scpi_write_terminator: bytes = b"\n"
    scpi_read_terminator: bytes = b"\n"
    maximum_scpi_response_bytes: int = 4096
    maximum_error_queue_entries: int = 32
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    reconnect: ReconnectPolicy = field(default_factory=ReconnectPolicy)
    safety: SafetyPolicy = field(default_factory=SafetyPolicy)
```

**[API-006]** Implementation may add keyword-only fields, but shall not remove, rename, or change the meaning of fields above before v2.0. Validation shall reject infinite, non-finite, negative, contradictory, or unsafe values before opening the port.

### 9.4 Exact identity, capability, measurement, and status models

```python
@dataclass(frozen=True, slots=True)
class InstrumentIdentity:
    manufacturer: str
    model: str
    serial_number: str
    firmware_revision: str
    raw: str

@dataclass(frozen=True, slots=True)
class InstrumentCapabilities:
    model: str
    firmware_revision: str
    protocol: Protocol
    maximum_voltage_v: float
    maximum_current_a: float
    maximum_power_w: float
    minimum_voltage_v: float | None
    minimum_resistance_ohm: float | None
    maximum_resistance_ohm: float | None
    supported_features: frozenset[str]
    experimental_features: frozenset[str]
    evidence_ids: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class Measurement:
    value: float
    unit: str
    monotonic_timestamp_s: float
    wall_timestamp_utc: datetime
    protocol: Protocol
    valid: bool
    raw: str | bytes | None = None

@dataclass(frozen=True, slots=True)
class MeasurementSnapshot:
    voltage: Measurement
    current: Measurement
    power: Measurement
    resistance: Measurement | None
    status: DeviceStatus | None

@dataclass(frozen=True, slots=True)
class AppliedSetpoint:
    requested: float
    applied: float
    unit: str
    wire_value: int | str
    verified: bool

@dataclass(frozen=True, slots=True)
class DeviceStatus:
    input_enabled: bool | None
    short_enabled: bool | None
    operating_mode: OperatingMode | None
    status_byte: int | None
    questionable_condition: int | None
    operation_condition: int | None
    protection_flags: ProtectionFlag
    unknown_bits: int
    synchronized: bool
```

**[API-007]** `DiagnosticSnapshot`, `HealthReport`, audit events, and command outcomes shall be JSON-serializable through explicit `to_dict()` methods; they shall not rely on serializing internal locks, transports, or exceptions directly.

### 9.5 Identification and capabilities

```python
    def identify(self) -> InstrumentIdentity: ...
    def get_scpi_version(self) -> str: ...
    def get_capabilities(self, *, refresh: bool = False) -> InstrumentCapabilities: ...
```

**[API-008]** Unknown instruments may be connected for `identify`, diagnostics, and raw read-only operations. All hazardous high-level operations shall remain blocked unless `SafetyPolicy.block_unknown_model_hazards` is disabled explicitly.

### 9.6 Common/status operations

```python
    def clear_status(self) -> None: ...
    def set_event_status_enable(self, value: int) -> None: ...
    def get_event_status_enable(self) -> int: ...
    def read_event_status_register(self) -> int: ...
    def operation_complete(self, *, timeout_s: float | None = None) -> None: ...
    def is_operation_complete(self, *, timeout_s: float | None = None) -> bool: ...
    def set_power_on_status_clear(self, enabled: bool) -> None: ...
    def get_power_on_status_clear(self) -> bool: ...
    def save_state(self, slot: int) -> None: ...
    def recall_state(self, slot: int) -> None: ...
    def reset_device(self) -> None: ...
    def set_service_request_enable(self, value: int) -> None: ...
    def get_service_request_enable(self) -> int: ...
    def read_status_byte(self) -> int: ...
    def self_test(self, *, timeout_s: float | None = None) -> SelfTestResult: ...
```

**[API-009]** `reset_device`, `recall_state`, and `save_state` are high-impact operations and shall never run during connect, reconnect, synchronization, or cleanup.

### 9.7 Input, mode, range, and setpoint operations

```python
    def get_input_enabled(self) -> bool: ...
    def set_input_enabled(self, enabled: bool, *, token: SafetyToken | None = None) -> None: ...
    def get_short_enabled(self) -> bool: ...
    def set_short_enabled(self, enabled: bool, *, token: SafetyToken) -> None: ...

    def get_operating_mode(self) -> OperatingMode: ...
    def set_operating_mode(self, mode: OperatingMode) -> None: ...

    def get_current_setpoint(self) -> float: ...
    def set_current_setpoint(self, amperes: float) -> AppliedSetpoint: ...
    def get_voltage_setpoint(self) -> float: ...
    def set_voltage_setpoint(self, volts: float) -> AppliedSetpoint: ...
    def get_power_setpoint(self) -> float: ...
    def set_power_setpoint(self, watts: float) -> AppliedSetpoint: ...
    def get_resistance_setpoint(self) -> float: ...
    def set_resistance_setpoint(self, ohms: float) -> AppliedSetpoint: ...

    def get_current_range(self) -> float: ...
    def set_current_range(self, amperes: float) -> AppliedSetpoint: ...
    def get_voltage_range(self) -> float: ...
    def set_voltage_range(self, volts: float) -> AppliedSetpoint: ...
    def get_voltage_autorange(self) -> bool: ...
    def set_voltage_autorange(self, enabled: bool) -> None: ...

    def get_current_slew(self) -> SlewRate: ...
    def set_current_slew(self, value: float) -> AppliedSetpoint: ...
    def set_current_slew_rise(self, value: float) -> AppliedSetpoint: ...
    def set_current_slew_fall(self, value: float) -> AppliedSetpoint: ...

    def get_remote_sense(self) -> bool: ...
    def set_remote_sense(self, enabled: bool) -> None: ...
    def get_load_on_voltage(self) -> float: ...
    def set_load_on_voltage(self, volts: float) -> AppliedSetpoint: ...
    def get_load_off_voltage(self) -> float: ...
    def set_load_off_voltage(self, volts: float) -> AppliedSetpoint: ...
```

**[API-010]** A state-changing setter shall either return a verified `AppliedSetpoint`, return an unverified value with `verified=False` only when explicitly permitted by the command policy, or raise a structured exception. It shall never silently clamp.

### 9.8 Measurement operations

```python
    def measure_voltage(self) -> Measurement: ...
    def measure_voltage_maximum(self) -> Measurement: ...
    def measure_voltage_minimum(self) -> Measurement: ...
    def measure_voltage_peak_to_peak(self) -> Measurement: ...
    def measure_current(self) -> Measurement: ...
    def measure_current_maximum(self) -> Measurement: ...
    def measure_current_minimum(self) -> Measurement: ...
    def measure_current_peak_to_peak(self) -> Measurement: ...
    def measure_power(self) -> Measurement: ...
    def measure_resistance(self) -> Measurement: ...
    def measure_all(self) -> MeasurementSnapshot: ...
```

**[API-011]** Measurement parsing shall reject malformed, oversized, non-finite, or semantically impossible responses and shall preserve bounded raw diagnostic context.

### 9.9 Compound safety operation

```python
@dataclass(frozen=True, slots=True)
class SafeEnableConfig:
    mode: OperatingMode
    setpoint: float
    current_limit_a: float | None = None
    voltage_limit_v: float | None = None
    power_limit_w: float | None = None
    resistance_limit_ohm: float | None = None
    remote_sense: bool = False
    verify: bool = True

@dataclass(frozen=True, slots=True)
class SafeEnableResult:
    input_enabled: bool
    input_off_after_failure: bool | None
    applied_setpoint: AppliedSetpoint
    status: DeviceStatus
    audit_event_id: str

class BK8500B:
    def configure_and_enable(
        self,
        config: SafeEnableConfig,
        *,
        token: SafetyToken | None = None,
    ) -> SafeEnableResult: ...
```

**[API-012]** The method shall implement the state machine in section 7.7.3. The agent shall not expose a convenience method that combines configuration and enable without the same validation and rollback semantics.

### 9.10 Advanced stable configurations

**[API-013]** The following dataclasses and methods are frozen at the type/name level. Their fields shall be finalized in `docs/public_api_contract.md` before Gate G4 and may only include values represented in the command-policy matrix.

```python
    def configure_transient(self, config: TransientConfig) -> None: ...
    def get_transient_config(self) -> TransientConfig: ...
    def configure_led(self, config: LEDConfig) -> None: ...
    def get_led_config(self) -> LEDConfig: ...
    def configure_ocp_test(self, config: OCPTestConfig) -> None: ...
    def run_ocp_test(self, *, timeout_s: float | None = None) -> OCPTestResult: ...
    def configure_timing_test(self, config: TimingTestConfig) -> None: ...
    def run_timing_test(self, *, timeout_s: float | None = None) -> TimingTestResult: ...
    def configure_list(self, config: ListConfig) -> None: ...
    def run_list(self, *, timeout_s: float | None = None) -> ListRunResult: ...
    def trigger(self) -> None: ...
    def clear_protection(self, *, token: SafetyToken) -> None: ...
```

**[API-014]** A compound configuration shall validate every field and capability before the first write. If the protocol cannot apply a compound configuration atomically, the method shall document and test its rollback/reconciliation behavior.

### 9.11 Status and error API

```python
    def get_device_status(self) -> DeviceStatus: ...
    def read_questionable_event(self) -> int: ...
    def read_questionable_condition(self) -> int: ...
    def set_questionable_enable(self, value: int) -> None: ...
    def get_questionable_enable(self) -> int: ...
    def read_operation_event(self) -> int: ...
    def read_operation_condition(self) -> int: ...
    def set_operation_enable(self, value: int) -> None: ...
    def get_operation_enable(self) -> int: ...
    def read_next_error(self) -> SCPIErrorEntry: ...
    def drain_error_queue(self, *, maximum: int | None = None) -> tuple[SCPIErrorEntry, ...]: ...
```

**[API-015]** Unknown status bits shall be preserved. Event-register methods shall document destructive-read behavior.

### 9.12 Experimental API boundary

**[API-016]** Battery and autotest functions shall initially exist only under `bk8500b.experimental`. Experimental objects shall require explicit import, include an `experimental=True` marker in diagnostics, and shall not be re-exported from `bk8500b.__init__`.

### 9.13 Raw access

```python
    def write_raw_scpi(self, command: str, *, timeout_s: float | None = None) -> None: ...
    def query_raw_scpi(self, command: str, *, timeout_s: float | None = None) -> str: ...
    def transact_raw_legacy(self, frame: bytes, *, timeout_s: float | None = None) -> bytes: ...
```

**[API-017]** Raw methods shall invalidate all cached device state, bypass high-level verification, emit a high-severity audit event, and be excluded from safety guarantees. They shall never be used internally by high-level methods; internal protocol calls shall use non-public typed command objects.

### 9.14 Asynchronous facade

**[API-018]** `AsyncBK8500B` shall expose asynchronous counterparts with the same names, argument semantics, return models, and exceptions. It shall delegate to one serialized worker around the synchronous engine. Cancellation semantics shall follow section 7.7.2; cancellation shall not imply that a command was not transmitted.

### 9.15 Compatibility policy

**[API-019]** Gate G3 shall generate an API snapshot test that inspects public exports, constructor signatures, method signatures, dataclass fields/order/defaults, enum members, and exception inheritance. The snapshot shall be reviewed and stored in `tests/api_contract/v1_0.json`.

- Removing or renaming a stable symbol requires a major version.
- Adding optional keyword-only parameters is allowed in a minor version.
- Changing a default that affects safety, transport framing, retry, or verification requires an ADR and major version unless it only tightens safety without breaking documented workflows.
- **[API-020]** Experimental API may change in minor releases but shall carry explicit migration notes.
- **[API-021]** Deprecations shall remain for at least one minor release and emit `DeprecationWarning`.

## 10. Units, scaling, and numeric behavior

### 10.1 Public units

Use SI units in the public API:

- Volts.
- Amperes.
- Watts.
- Ohms.
- Seconds.
- Amperes per microsecond for the manufacturer-defined slew-rate values, while documenting the instrument unit explicitly.

### 10.2 Integer wire representation

**[PROTO-LEG-001]** Legacy wire values shall be converted through explicit scale definitions. Known manual scales include:

| Quantity | Legacy count scale |
|---|---:|
| Voltage | 1 mV/count |
| Current | 0.1 mA/count |
| Power | 1 mW/count |
| Resistance | 1 mΩ/count, inferred from documented examples and requiring HIL confirmation |
| Transient dwell | 0.1 ms/count |
| Load-on timer | 1 s/count |

No scaling may be copied from a neighboring command without an explicit evidence record.

### 10.3 Deterministic quantization

Convert user values through `Decimal(str(value))` or an equivalent deterministic method. Use a documented rounding rule, preferably round-half-up, and return the actual quantized value applied by the driver.

**[PROTO-LEG-002]** Never silently clamp a value. Out-of-range values shall raise `InstrumentRangeError` unless the caller explicitly requests a separately named clamp helper.

Reject:

- NaN.
- Positive or negative infinity.
- **[PROTO-LEG-003]** Negative values where prohibited.
- Boolean values passed as numeric setpoints.
- Values exceeding model, range, or protocol field limits.

---

## 11. SCPI protocol requirements

### 11.1 Terminators

**[PROTO-SCPI-005]** The supplied manual does not define command/response terminators. The implementation shall:

- Make write and read terminators configurable.
- Use LF as the provisional default only when documented as such in `protocol_assumptions.md`.
- Offer a diagnostic terminator probe based solely on harmless queries.
- Clear/reopen the transport between failed probe variants.

### 11.2 Response limits

**[PROTO-SCPI-006]** Every SCPI query shall enforce:

- Finite timeout.
- Maximum response length.
- Valid text decoding.
- No embedded NUL unless explicitly expected.
- Command-specific parsing.

### 11.3 Error handling

**[PROTO-SCPI-007]** High-level state-changing methods shall optionally query the SCPI error queue after a transaction according to configuration. Error draining shall stop when `0, No Error` is seen or when the configured maximum number of entries is reached.

**[PROTO-SCPI-008]** Error-queue overflow shall be surfaced distinctly.

### 11.4 Command pacing

**[PROTO-SCPI-009]** The executor shall enforce a configurable minimum inter-command delay. The provisional default shall be conservative and must be adjusted by hardware validation. Only one query may be outstanding.

### 11.5 SCPI command aliases

Use canonical long-form commands internally where practical. Do not depend on apparent typographical errors in the converted manual, such as `SSTATus`, without validation.

---

## 12. Legacy binary protocol requirements

### 12.1 Frame structure

Implement a fixed 26-byte frame:

| Byte index | Meaning |
|---:|---|
| 0 | Start byte `0xAA` |
| 1 | Instrument address |
| 2 | Command byte |
| 3–24 | Command payload/reserved bytes |
| 25 | Checksum |

### 12.2 Checksum

The provisional checksum algorithm is:

```text
checksum = sum(frame[0:25]) modulo 256
```

**[PROTO-LEG-004]** This shall be implemented as a pure function with exhaustive and property-based tests. It shall remain marked as provisional until confirmed by real hardware or an official unambiguous source.

### 12.3 Framing and resynchronization

**[PROTO-LEG-005]** The decoder shall:

- Read exactly 26 bytes by a deadline.
- Correctly handle partial serial reads.
- Search for `0xAA` only within a bounded recovery buffer.
- Reject invalid checksum.
- Validate address.
- Validate command/response relationship where known.
- Preserve raw frame bytes in diagnostic exceptions.
- Cap discarded bytes to prevent endless resynchronization.

### 12.4 Broadcast address

**[PROTO-LEG-006]** Address `0xFF` shall be treated as broadcast only where explicitly allowed. Broadcast reads shall be prohibited. Broadcast writes shall be disabled by default and require `allow_broadcast_writes=True` plus an explicitly named API.

### 12.5 Device return codes

The manual lists response codes including:

- `0x80` success.
- `0x90` checksum error.
- `0xA0` invalid/out-of-range parameter.
- `0xB0` command not executable.
- `0xC0` invalid command.

**[PROTO-LEG-007]** The exact response-byte location and relationship to returned data shall be verified on hardware before stable release. Until verified, expose the raw response and treat unrecognized layouts as `LegacyProtocolError` rather than guessing.

### 12.6 Request idempotency

**[PROTO-LEG-008]** Every legacy command catalog entry shall classify the operation as:

- Read-only/idempotent.
- Idempotent state set.
- Non-idempotent or outcome-sensitive.
- Hazardous.

This classification controls retries and audit logging.

---

## 13. Timeouts, retries, and uncertain outcomes

### 13.1 Bounded operations

**[EXEC-001]** Every transport and device operation shall accept or inherit a finite deadline. Nested operations shall consume the parent deadline rather than restarting the full timeout for each internal step.

### 13.2 Retry policy

Automatic retries may be used for:

- Harmless read-only queries.
- Identity and status queries.
- Idempotent state-setting commands only when the previous attempt is proven not to have been accepted, or when query-after-write verification makes the result safe.

**[EXEC-002]** Automatic retries shall not be used blindly for:

- Input ON/OFF after a write timeout.
- Short-circuit enable/disable after a write timeout.
- Trigger commands.
- Save/recall commands.
- Reset.
- Protection clear.
- Step advancement or other non-idempotent actions.

### 13.3 Indeterminate result

If transport failure occurs after bytes may have been sent but before acknowledgement is validated, raise `IndeterminateCommandOutcome` containing:

- Command name.
- Whether all bytes were written.
- Whether any response bytes were received.
- Recommended state-verification query.
- Session health state.

**[EXEC-003]** The driver shall not claim the command failed or succeeded without evidence.

### 13.4 Backoff

**[EXEC-004]** Retryable failures shall use configurable bounded exponential backoff with jitter. The retry budget shall be finite and observable.

---

## 14. Reconnection and state recovery

### 14.1 Reconnection policy

**[EXEC-005]** Automatic reconnection shall be configurable and disabled for hazardous workflows unless the caller enables it knowingly.

### 14.2 Safe post-reconnect behavior

**[EXEC-006]** After reconnecting, the driver shall:

1. Re-identify the instrument.
2. Confirm model/serial match the original session.
3. Query input, mode, setpoints, protection status, and remote-sense state where possible.
4. Never automatically turn input ON.
5. Never automatically clear protection.
6. Never automatically replay a trigger.
7. Mark cached state invalid until verified.
8. Emit a recovery event/audit record.

If a different serial number is detected, abort recovery.

### 14.3 Configuration restoration

Non-hazardous configuration restoration may be enabled explicitly. Default behavior is to report current device state and require application-level reconciliation.

---

## 15. Electrical-safety behavior

### 15.1 Mandatory defaults

- Input remains OFF unless explicitly enabled by the caller.
- Short-circuit mode remains OFF unless explicitly enabled.
- No automatic reset or recall on connect.
- No automatic protection clear.
- No automatic use of broadcast.
- No automatic restoration of an ON state after reconnect.

### 15.2 Safe enable transaction

Provide a high-level `configure_and_enable()` or similarly named operation that:

1. Reads current input state.
2. Requires or forces input OFF before configuration according to policy.
3. Validates model ratings and requested limits.
4. Sets operating mode.
5. Sets current/voltage/power/resistance limit and setpoint as applicable.
6. Sets protection values.
7. Configures remote sense only when requested.
8. Reads back critical state.
9. Checks active protection/status flags.
10. Enables input only as the final step.
11. Confirms resulting input state.

**[SAFE-001]** On any pre-enable failure, input shall remain OFF.

### 15.3 Close behavior

**[SAFE-002]** `turn_input_off_on_close` shall be configurable. When enabled, close shall make a bounded best-effort OFF command and verify when possible. Documentation shall state clearly that software cannot guarantee shutdown after cable removal, host crash, instrument failure, or power loss.

For unattended hazardous tests, recommend use of external hardware interlocks, source current limiting, emergency-off hardware, and the instrument load-on timer where applicable.

### 15.4 Short-circuit mode

**[SAFE-003]** Short-circuit enable is a high-risk operation. It shall:

- Have an explicit method name.
- Never be called by generic mode helpers.
- Require input-state awareness.
- Be audit logged.
- Never be automatically retried after uncertain transmission.

---

## 16. State cache policy

**[SAFE-004]** Caching may reduce queries but shall never be treated as authoritative after:

- Reconnect.
- Timeout.
- Protocol parse error.
- Raw command.
- Local front-panel access.
- State recall/reset.
- Protection trip.

**[SAFE-005]** Each cached field shall carry a validity flag and timestamp. High-risk operations shall query real state rather than relying only on cache.

---

## 17. Exception hierarchy

Implement this exact public exception hierarchy:

```text
BK8500BError
├── ConfigurationError
├── InvalidStateTransitionError
├── LockTimeoutError
├── UnsupportedModelError
├── UnsupportedFeatureError
├── TransportError
│   ├── PortBusyError
│   ├── ConnectionLostError
│   ├── ReadTimeoutError
│   └── WriteTimeoutError
├── ProtocolError
│   ├── SCPIProtocolError
│   ├── LegacyProtocolError
│   ├── ChecksumError
│   ├── FrameSyncError
│   ├── MalformedResponseError
│   └── ResponseTooLargeError
├── DeviceError
│   ├── SCPICommandError
│   ├── ProtectionTrippedError
│   └── DeviceRejectedCommandError
├── InstrumentRangeError
├── UnsafeOperationError
└── IndeterminateCommandOutcome
```

**[API-022]** Exceptions shall preserve the original cause and useful structured context without exposing mutable internal objects.

---

## 18. Observability and diagnostics

### 18.1 Logging

Use standard Python logging. Do not configure global handlers from the library.

**[OBS-001]** Structured log fields shall include where applicable:

- Instrument model and serial number.
- Port/resource.
- Protocol.
- Command category, not necessarily the full command payload.
- Duration.
- Attempt count.
- Timeout/deadline.
- Reconnect count.
- Result category.
- Protection/status summary.

**[OBS-002]** Raw SCPI and hex-frame traces shall be disabled by default and enabled only through an explicit diagnostic setting.

### 18.2 Audit events

Generate audit events for:

- Input ON/OFF.
- Short ON/OFF.
- Mode change.
- Setpoint/limit/protection change.
- Reset.
- Save/recall.
- Trigger.
- Protection clear.
- Reconnect and identity mismatch.

Expose callbacks or a lightweight event sink. Do not force file logging.

### 18.3 Metrics hooks

Expose optional counters/timers without requiring a metrics framework:

- Commands attempted/succeeded/failed.
- Timeouts.
- Retries.
- Reconnects.
- Checksum/framing errors.
- SCPI errors.
- Protection trips.
- Command latency.
- Consecutive health-check failures.

### 18.4 Diagnostic snapshot

Provide a serializable diagnostic snapshot containing configuration with safe redaction, identity, capabilities, protocol state, current health, last error, counters, status registers, and recent audit-event summaries.

---

## 19. CLI requirements

Install a CLI entry point, for example `bk8500b`.

Required commands:

- `ports` — list candidate serial ports without transmitting.
- `probe` — explicitly probe a selected port using safe read-only operations.
- `info` — identity and capabilities.
- `measure` — one-shot or bounded polling.
- `status` — decoded status registers.
- `errors` — read/drain error queue with a limit.
- `self-test` — execute self-test with warning.
- `diagnose` — produce a diagnostic report.
- `raw-scpi` — advanced explicit command.
- `raw-legacy` — advanced explicit frame transaction.

**[API-023]** The CLI shall not scan and transmit to all serial ports by default. Commands that may enable load, short, reset, recall, clear protection, or trigger shall require explicit subcommands and confirmation-bypass flags suitable for automation.

---

## 20. Command catalog, policy matrix, and traceability

### 20.1 Complete command inventory

**[AGENT-001]** The implementation shall inventory every supplied command in these groups:

- 12 IEEE/common commands.
- 6 status-register commands.
- 10 measurement commands.
- 3 CR-LED parameter commands.
- 8 OCP-test commands.
- 6 peak-test commands.
- 26 input/mode/range/setpoint/dynamic commands.
- 6 system commands.
- 4 voltage rise/fall commands.
- 12 timing-test commands.
- All legacy command IDs in sections 12.1 through 12.75, including paired set/read IDs.

**[AGENT-002]** No command may disappear from the inventory. Unresolved commands shall be marked `BLOCKED` or `EXPERIMENTAL`; they shall not receive a guessed implementation.

### 20.2 Mandatory command-policy matrix

**[AGENT-003]** Before implementing any high-level command, the agent shall create its row in `docs/command_policy_matrix.md`. The matrix is normative and shall contain these columns:

| Column | Required content |
|---|---|
| Requirement ID | Stable `PROTO-*`, `API-*`, or `SAFE-*` identifier |
| Manual reference | Section/page and source hash |
| Canonical command | Full SCPI syntax or legacy command ID |
| Public API method | Exact method from section 9 or `None` |
| Protocol | SCPI, legacy, or both |
| Direction | Query, idempotent write, non-idempotent action, compound operation |
| Risk class | `READ_ONLY`, `CONFIGURATION`, `OUTPUT_CONTROL`, `SHORT`, `RESET_RECALL`, `TRIGGER_TEST`, or `RAW` |
| Preconditions | Session state, input state, mode, capability, token, range |
| Parameter model | Exact type, unit, range source, and quantization |
| Wire encoding | Terminator/field offsets/endianness/scale |
| Response model | Exact parser and allowed response length |
| Timeout class | `NORMAL`, `LONG_OPERATION`, or explicit override |
| Idempotency | `YES`, `NO`, or `CONDITIONAL` with rationale |
| Automatic retry | Exact permitted failures and maximum attempts |
| Indeterminate handling | Verification query or mandatory exception |
| Readback verification | Query, tolerance, and mismatch behavior |
| Cache effects | Fields updated or invalidated |
| Error mapping | Device/protocol errors and exceptions |
| Audit event | Event type and redaction behavior |
| Capability gate | Model/firmware/protocol evidence |
| Stability | `STABLE`, `EXPERIMENTAL`, `BLOCKED`, `UNSUPPORTED` |
| Unit tests | Test IDs |
| Integration/HIL evidence | Test and capture IDs |

**[AGENT-004]** A row with unknown wire encoding, response model, risk classification, or indeterminate handling shall not be promoted to `STABLE`.

### 20.3 Required baseline policies

**[AGENT-005]** The following policies are fixed and shall appear in the matrix:

| Operation | Risk | Automatic retry | Required outcome verification |
|---|---|---|---|
| Identity/version/rating query | Read-only | One bounded retry after clean resynchronization | Parse and identity consistency |
| Measurement query | Read-only | One bounded retry on timeout/framing error when no stale bytes remain | Valid finite response |
| Status-condition query | Read-only | One bounded retry | Valid register range |
| Destructive event/error read | Read-only but destructive | No automatic retry unless protocol proves no response was consumed | Caller receives indeterminate/destructive-read warning |
| Set current/voltage/power/resistance | Configuration | No blind write retry | Query corresponding setpoint and compare quantized value |
| Range/slew/limit/sense change | Configuration | No blind write retry | Query corresponding state where supported |
| Input OFF | Output control | No blind retry after uncertain write; one verification query | `INPut? == OFF` or indeterminate outcome |
| Input ON | Output control | Never | `INPut? == ON`; failure invokes bounded best-effort OFF |
| Short ON/OFF | Short | Never | Explicit short-state query or indeterminate outcome |
| Reset/recall/save | Reset/recall | Never | Re-identify and resynchronize; save may only verify via documented evidence |
| Trigger/start OCP/start timing/start list | Trigger/test | Never | Operation-specific status/result query |
| Protection clear | Output-affecting action | Never | Re-read protection/status registers |
| Raw command | Raw | Never | No high-level inference; invalidate cache |

### 20.4 Requirements traceability matrix

**[AGENT-006]** `docs/requirements_traceability.md` shall contain one row per requirement identifier with:

- Requirement text and source section.
- Source-manual command/reference or `N/A` for software-only requirements.
- Implementation module/class/function owner.
- Command-policy row identifier when applicable.
- Unit, integration, property, fault-injection, and HIL test IDs.
- Evidence artifact path.
- Gate first required.
- Current status: `NOT_STARTED`, `IMPLEMENTED`, `VERIFIED_SIMULATED`, `VERIFIED_HARDWARE`, or `BLOCKED`.

**[AGENT-007]** Gate completion is prohibited while any requirement assigned to that gate lacks a verification method or has an unresolved `BLOCKED` status without an approved scope exclusion.

### 20.5 Stable versus experimental promotion

A command may enter the stable API only when:

1. Frame or SCPI syntax is unambiguous.
2. Units/scaling and quantization are known.
3. Range behavior and runtime limit source are known.
4. Response parsing and maximum response size are known.
5. Error behavior and destructive-read semantics are known.
6. Idempotency, retry, and indeterminate-outcome policy are complete.
7. Unit and fault-injection tests exist.
8. Hardware validation exists for at least one applicable model/firmware.
9. Safety classification, audit behavior, and cache effects are complete.
10. Traceability contains no missing owner, test, or evidence field.

### 20.6 Initial traceability examples

**[AGENT-008]** The Gate G0 document shall include at least the following rows and then expand them to all requirements:

| Requirement ID | Requirement summary | Source | Implementation owner | Verification | Gate |
|---|---|---|---|---|---|
| `SAFE-001` | Connection and probing never enable input | Sections 4.3, 5.3, 15.1 | `device.py`, `safety.py` | `TEST-SAFE-001`, `HIL-SAFE-001` | G3/G7 |
| `EXEC-001` | One in-flight request and finite parent deadline | Sections 7.3, 13.1 | `execution.py` | `TEST-EXEC-001..006` | G1/G5 |
| `EXEC-002` | Uncertain state-changing write is never blindly retried | Sections 7.7.2, 13.3 | `execution.py` | `TEST-FAULT-010..018`, `HIL-FAULT-003` | G5/G7 |
| `PROTO-LEG-001` | Legacy frame is exactly 26 bytes | Section 12.1 | `legacy_codec.py` | golden/property tests and capture `CAP-LEG-001` | G2/G7 |
| `API-001` | Public constructor and lifecycle match section 9.2 | Section 9.2 | `device.py` | API signature snapshot | G3 |
| `REL-001` | 168-hour soak passes release thresholds | Section 24 | test harness/release docs | `SOAK-168H-001` | G8 |

## 21. Manual ambiguity register

**[AGENT-009]** The agent shall create and maintain a formal ambiguity register. The initial entries shall include at least the following.

| ID | Issue | Required treatment |
|---|---|---|
| A-001 | SCPI command and response terminators are absent. | Configurable terminators; safe probe; HIL validation. |
| A-002 | Data bits and stop bits are not stated in the supplied programming manual. | Configurable; provisional 8N1; validate. |
| A-003 | `*RCL` documents slots 0–9 while `*SAV` documents 0–99. | Do not assume symmetry; test slots; document per firmware. |
| A-004 | `*PSC` Boolean wording/order is ambiguous. | Validate ON/OFF readback before stable support. |
| A-005 | `SSTATus` appears to be a typographical error. | Use canonical `STATus` only after validation. |
| A-006 | Several SCPI parameter tables contain missing or contradictory parameter descriptions. | Derive only from explicit syntax and HIL results; no silent inference. |
| A-007 | SCPI protection descriptions refer to delay commands not documented in the command list. | Mark unsupported until an official command source is found. |
| A-008 | Legacy checksum modulo behavior is implied but not explicit. | Implement provisional modulo-256 and confirm. |
| A-009 | One legacy section says checksum byte 27 although frame length is 26. | Treat as typo; verify all responses are 26 bytes. |
| A-010 | Address ranges vary between 0–31, 0–0xFE, and broadcast 0xFF. | Stable device address range 0–31; restrict broadcast. |
| A-011 | Legacy voltage example for 16.000 V is inconsistent (`0x3E80` versus `0x3EB0`). | Use mathematically correct 16000-count vector and confirm on hardware. |
| A-012 | Legacy list repeat mode places `65535` in what appears to be one byte. | Block unlimited-repeat support until field width is confirmed. |
| A-013 | Some reserved-byte ranges omit bytes or overlap. | Build each codec only from verified offsets. |
| A-014 | D8H/89H appears instead of D8H/D9H in one heading. | Treat D9H as provisional read command and validate. |
| A-015 | Autotest chain and save/recall command IDs conflict in headings. | Use body IDs only provisionally; require HIL captures. |
| A-016 | Von value length and scale are unclear. | Keep experimental until resolved. |
| A-017 | Legacy return-code byte location is not clearly specified. | Do not guess; capture and document responses. |
| A-018 | Many advanced legacy values lack explicit unit scales. | Keep affected functions experimental or blocked. |
| A-019 | Mixing SCPI and legacy protocols in one session is not documented. | Prohibit by default. |
| A-020 | Converted Markdown contains OCR/table corruption and missing spacing. | Cross-check against original PDF before release. |
| A-021 | Front-panel/local changes can invalidate host-side state. | Conservative cache invalidation and state query before hazards. |
| A-022 | Maximum safe command rate is not specified. | Configurable pacing and soak-test determination. |
| A-023 | Behavior after cable loss while input is ON is not specified. | Document limitation; no false fail-safe claim. |
| A-024 | Model/firmware feature differences are not fully enumerated. | Runtime capabilities and per-model HIL matrix. |

No ambiguity may be “resolved” only by making code compile.

---

## 22. Testing requirements

### 22.1 Unit tests

Test every public method, validation rule, parser, status decoder, and error mapping without hardware by using fake transports.

### 22.2 Protocol golden vectors

Create golden-vector tests for:

- 26-byte frame construction.
- Checksum.
- Address and command positions.
- 16.000 V encoding as 16000 counts (`0x00003E80`, little-endian payload).
- 3.0000 A encoding as 30000 counts (`0x00007530`).
- 200.000 W encoding as 200000 counts (`0x00030D40`).
- 200.000 Ω provisional encoding as 200000 counts.
- Transient dwell fields.
- Status-bit decoding.
- Return-code parsing after HIL validation.

### 22.3 Property-based tests

Use property tests for:

- Encode/decode round trips across valid ranges.
- Checksum invariants.
- Partial-read reconstruction.
- Random leading garbage and bounded frame resynchronization.
- Numeric quantization boundaries.
- Rejection of overflow and non-finite values.

### 22.4 Fault-injection tests

Simulate:

- Port busy.
- Disconnect before write.
- Disconnect during write.
- Disconnect after write before response.
- Partial response.
- Delayed response.
- Extra/stale response bytes.
- Wrong checksum.
- Wrong address.
- Wrong command ID.
- Random garbage before frame.
- Oversized SCPI response.
- Missing terminator.
- Invalid UTF-8/ASCII.
- SCPI error queue overflow.
- Reconnect to a different serial number.
- Concurrent calls from multiple threads.
- Cancellation during a long operation.

### 22.5 Static quality checks

Required:

- Strict type checking for production modules.
- Linting and formatting in CI.
- No unresolved high-severity security findings.
- No ignored broad exceptions without documented reason.
- No busy-wait loops.
- No infinite retry loops.
- No library-installed global signal handlers.

### 22.6 Coverage targets

Minimum release targets:

- 95% statement coverage for production package.
- 90% branch coverage for production package.
- 100% branch coverage for checksum, frame codec, scaling, and safety precondition modules.
- Every exception class exercised.

Coverage numbers do not replace HIL testing.

---

## 23. Hardware-in-the-loop validation

### 23.1 Required bench

Use at least one real supported 8500B-series load. Final family release should test every available model class or document untested models clearly.

For load-enabled tests, use:

- Current-limited low-voltage source.
- Appropriately rated wiring and fusing.
- Emergency disconnect.
- Conservative power/current levels.
- Independent DMM or power analyzer for selected verification points.

### 23.2 Mandatory HIL cases

Validate:

1. Port open/close and exclusive ownership.
2. SCPI identity and version.
3. Legacy read-only identification/rating command.
4. All configured terminator variants.
5. DTR/RTS behavior.
6. Address handling.
7. Input OFF at driver connect.
8. CC/CV/CW/CR set/get at safe levels.
9. Measurements against an independent instrument.
10. Status and error queue.
11. Protection trip and explicit clear.
12. Remote-sense disconnect status where safe.
13. Dynamic operation.
14. Peak/OCP/LED/timing operations.
15. List operation.
16. Battery/autotest experimental commands.
17. Cable disconnect at multiple transaction phases.
18. Reconnect and identity verification.
19. Front-panel change followed by state resynchronization.
20. Clean shutdown and repeated open/close cycles.

### 23.3 Protocol capture

Store sanitized request/response hex captures for every legacy command promoted to stable. Include instrument model, serial redaction policy, firmware, baud, address, expected physical state, and observed result.

---

## 24. 24/7 soak and endurance requirements

### 24.1 Pre-release soak

Run a minimum 168-hour continuous HIL soak test before production release.

Suggested workload:

- Measurement snapshot at 1 Hz.
- Status query at 0.2 Hz.
- Error-queue check at 0.02 Hz.
- Controlled setpoint changes at safe levels.
- Planned reconnect every 6 hours.
- Simulated transient serial faults.
- Periodic local/front-panel state change if allowed.

### 24.2 Acceptance criteria

During the 168-hour run:

- No uncaught exception terminates the supervisory process.
- No deadlock.
- No permanently stuck worker thread.
- No file-descriptor/handle leak.
- **[REL-005]** Resident memory growth after warm-up shall remain below 25 MiB, unless a measured, documented platform effect justifies another limit.
- Internal command queues remain bounded.
- Every injected recoverable fault produces a bounded recovery or a clear terminal session state.
- No automatic input ON after reconnect.
- No duplicate trigger/reset/save/recall caused by retry logic.
- All audit events remain ordered per session.
- **[REL-006]** Communication-success rate under stable-link periods shall be at least 99.9% for read-only polling, excluding deliberately injected faults.

### 24.3 Quantified operational service targets

**[REL-007]** Unless a command-policy row defines a stricter value, the implementation shall meet these defaults:

| Metric | Required target |
|---|---:|
| Normal query default deadline | 2.0 s |
| Normal write default deadline | 2.0 s |
| Connection deadline | 3.0 s |
| Lock-acquisition deadline | 5.0 s |
| Default close completion | ≤5.0 s |
| Long-operation default deadline | 120 s, explicitly overrideable and never infinite |
| Internal asynchronous queue | Bounded, default maximum 256 requests |
| Maximum SCPI response | 4096 bytes by default |
| Maximum error-queue drain | 32 entries by default |
| Reconnect attempts | Maximum 3 by default |
| Reconnect total elapsed budget | Maximum 15 s by default |
| Health-check consecutive failures before `DEGRADED` | 3 by default |
| Diagnostic snapshot deadline | ≤5.0 s, with partial-result marker if device queries fail |
| Worker/thread shutdown | No live driver-owned worker after close deadline plus 1.0 s cleanup allowance |
| Open/close endurance | At least 1,000 cycles without leaked handles or threads |
| Async cancellation | Session lock released on every terminal path; uncertain writes reported explicitly |
| Callback overhead | Audit/metrics callback shall not block the command engine for >10 ms; slower sinks require decoupling |
| Cache freshness | Age and validity exposed; no cached value represented as live after invalidation |

**[REL-008]** The agent may change provisional defaults only through an ADR backed by measurements and updated tests. Configuration shall expose the safety-relevant deadlines rather than hiding hard-coded values.

### 24.4 Extended qualification

For high-consequence production use, recommend a 30-day application-specific soak after the driver’s 168-hour qualification.

---

## 25. Documentation requirements

Generate and maintain:

1. `README.md` — purpose, supported models, safety warning, installation, quick start.
2. API reference with type signatures and examples.
3. Architecture document with a Mermaid component diagram and request lifecycle.
4. Command coverage matrix.
5. Protocol assumptions and ambiguities.
6. Safety guide.
7. 24/7 deployment and monitoring guide.
8. Troubleshooting guide, including TTL-adapter warning, COM-port ownership, baud/address/parity, DTR/RTS, and `separate` connection mode.
9. Hardware validation procedure and results template.
10. Release checklist.
11. Changelog.
12. Contributing and security-reporting guidance.

**[REL-009]** Documentation shall not promise electrical fail-safe behavior that software cannot guarantee.

---

## 26. Examples requirements

Provide runnable examples for:

- List ports without probing.
- Safe connection and identification.
- One-shot measurements.
- Continuous measurement polling with graceful shutdown.
- Safe CC configuration and input enable inside `try/finally`.
- CV, CW, and CR configuration.
- Dynamic/transient configuration.
- Protection/status monitoring.
- SCPI error handling.
- Long-running supervisor with reconnect.
- Async facade usage.
- Legacy list operation after validation.
- Diagnostic report generation.

**[REL-010]** Any example that enables input shall use conservative placeholder values, prominent warnings, and guaranteed best-effort disable in cleanup.

---

## 27. Packaging and compatibility

### 27.1 Python packaging

Use `pyproject.toml` with PEP 517/518/621-compatible metadata. Build both wheel and source distribution.

### 27.2 Supported Python versions

**[REL-011]** Target maintained CPython versions suitable for industrial systems, with a minimum of Python 3.10. The CI matrix shall include the project’s declared minimum and current supported versions.

### 27.3 Operating systems

Required CI and user documentation:

- Windows 11.
- Current Ubuntu LTS.

**[REL-012]** Linux permission troubleshooting shall cover dialout-group/udev issues without automatically changing system permissions from the library.

### 27.4 Installation verification

**[REL-013]** CI shall:

1. Build wheel and sdist.
2. Install each into a clean environment.
3. Import the package.
4. Run CLI `--help`.
5. Run unit tests against the installed wheel.
6. Validate package metadata and included documentation files.

---

## 28. Security and robustness

- Treat device responses as untrusted input.
- Cap all response sizes and error-queue loops.
- Never evaluate or execute response text.
- Avoid shell commands in the library.
- **[REL-014]** Avoid temporary files unless required by diagnostics; create them securely.
- Do not collect telemetry automatically.
- Do not transmit data over a network.
- Do not log full raw traffic by default.
- Use dependency pin ranges and automated dependency review in CI.
- Publish a vulnerability-reporting policy.

---

## 29. AI-agent implementation and deviation controls

### 29.1 Mandatory implementation behavior

**[AGENT-010]** The coding agent shall:

1. Read the complete specification and source-manual inventory before generating production code.
2. Generate `docs/requirements_traceability.md`, `docs/command_policy_matrix.md`, `docs/public_api_contract.md`, and `docs/state_machines.md` during Gate G0.
3. **[AGENT-011]** Preserve the root package layout and frozen public names; it shall not introduce `src/`.
4. Implement pure transport/protocol codecs before device semantics.
5. Add tests and traceability updates in the same change as each feature.
6. Never invent undocumented byte offsets, scales, response codes, terminators, ranges, or completion behavior.
7. Mark unresolved functions `BLOCKED` or `EXPERIMENTAL` rather than fabricating behavior.
8. Avoid placeholder methods, dummy success, empty exception handlers, hidden sleeps, and unbounded loops.
9. Avoid broad `except Exception` recovery that converts protocol or safety faults into success.
10. Avoid automatic hazardous actions during construction, connect, reconnect, synchronization, or close.
11. Preserve exact public API signatures after Gate G3.
12. Generate complete documentation, examples, package metadata, and reproducible commands.
13. Include a hardware-test matrix, capture index, ambiguity report, and release evidence bundle.
14. Refuse to label the package production-ready until every mandatory release gate passes.
15. Stop implementation of an affected stable feature when source evidence is insufficient; continue with unaffected work.

### 29.2 Architecture Decision Records

**[AGENT-012]** Any deviation from architecture, public API, requirement semantics, protocol assumption, safety rule, test threshold, dependency policy, or repository layout shall create an ADR in `docs/adr/NNNN-title.md` before the deviation is implemented.

**[AGENT-013]** Each ADR shall contain:

- Context and affected requirement IDs.
- Options considered.
- Decision and rationale.
- Safety and backward-compatibility impact.
- **[AGENT-014]** Required code, test, documentation, and migration changes.
- Approval status.
- Hardware evidence, when protocol behavior is affected.

**[AGENT-015]** An ADR shall not waive an electrical-safety requirement, hide an unresolved protocol ambiguity, or substitute opinion for HIL evidence.

### 29.3 Change-control rules

- **[AGENT-016]** A changed requirement shall update the specification version, traceability row, affected command-policy rows, tests, and changelog in one change set.
- **[AGENT-017]** A changed protocol assumption shall invalidate prior affected HIL evidence until reverified.
- **[AGENT-018]** A changed public API shall update `docs/public_api_contract.md` and compatibility tests.
- **[AGENT-019]** A changed timeout/retry policy shall include fault-injection and endurance evidence.
- **[AGENT-020]** Generated code shall not be accepted solely because tests written by the same generation pass; protocol golden vectors and independent invariants are required.

### 29.4 Prohibited implementation shortcuts

**[AGENT-021]** The agent shall not:

- Infer a wire field from a neighboring command without evidence.
- Retry a non-idempotent or hazardous operation because “it usually works.”
- silently clamp, coerce, or reinterpret user values.
- Use cached state as authoritative after reconnect, timeout, raw access, reset, recall, local operation, or protection trip.
- Claim HIL, soak, coverage, or compatibility results that were not actually executed.
- Promote experimental code to stable to satisfy a coverage percentage.
- change frozen public names merely for style preference.

## 30. Implementation gates

### Gate G0 — Source normalization

Deliver:

- Original-source inventory and hash.
- Requirement-ID inventory and complete traceability skeleton.
- Frozen public API contract document.
- Formal state-machine document.
- Normalized SCPI command catalog.
- Normalized legacy command catalog.
- Initial ambiguity register.
- Complete command-policy matrix schema with baseline high-risk rows.
- Model/interface matrix.
- ADR template and decision log.

Exit criteria:

- Every manual command is represented once in the command-policy matrix.
- Every normative requirement has an owner and verification method.
- Frozen API symbols and state transitions pass documentation validation.
- No undocumented assumption is embedded in code.

### Gate G1 — Package and transport foundation

Deliver:

- Project skeleton.
- Configuration model.
- Transport interface.
- pySerial transport.
- Port listing.
- Finite timeout/deadline utilities.
- Logging hooks.

Exit criteria:

- Repeated fake/open/close tests pass.
- Port-busy and timeout paths pass.
- Wheel installs cleanly.

### Gate G2 — Protocol engines

Deliver:

- SCPI transaction engine.
- Legacy codec and transaction engine.
- Scaling utilities.
- Parsers and exception mapping.
- Property and golden-vector tests.

Exit criteria:

- 100% codec/scaling branch coverage.
- Partial-read and corruption fault tests pass.

### Gate G3 — Stable core API

Deliver:

- Identification/capabilities.
- Common/status commands.
- Input/mode/setpoint/range/slew.
- Measurement.
- Error queue.
- Safety policy and safe-enable transaction.

Exit criteria:

- Complete fake-instrument integration tests.
- No implicit input enable.
- Stable API documentation and signature-compatibility tests complete.
- All Gate G3 requirements are linked to passing tests in the traceability matrix.

### Gate G4 — Advanced functions

Deliver:

- Dynamic, peak, OCP, LED, rise/fall, timing.
- Trigger and load-on timer.
- Legacy list.
- Experimental battery/autotest.

Exit criteria:

- All functions classified stable/experimental/blocked.
- All compound configurations validated atomically before writes.

### Gate G5 — Resilience and observability

Deliver:

- Retry classification.
- Indeterminate-outcome handling.
- Reconnect state machine.
- Health checks.
- Diagnostics, audit events, metrics hooks.
- Async facade.

Exit criteria:

- Fault-injection suite passes.
- Every transaction terminal state releases locks and records one outcome.
- No duplicate hazardous operation under timeout or cancellation tests.
- Reconnect and safe-enable state-transition coverage is complete.

### Gate G6 — Documentation and packaging

Deliver:

- Full documentation set.
- Examples.
- CLI.
- Build/release automation.
- License and security policy.

Exit criteria:

- Docs build without warnings.
- Traceability contains no orphan requirement, test, or implementation owner.
- Public API compatibility snapshot passes.
- Fresh-user installation test passes on Windows and Ubuntu.

### Gate G7 — Hardware validation

Deliver:

- HIL results.
- Protocol captures.
- Resolved ambiguity entries.
- Per-model/firmware feature matrix.
- Measurement comparison results.

Exit criteria:

- All stable commands have HIL evidence.
- No unresolved critical protocol ambiguity remains in stable API.

### Gate G8 — Endurance and release

Deliver:

- 168-hour soak logs and summary.
- Memory/handle analysis.
- Failure/recovery report.
- Final release checklist.
- Signed/tagged release artifacts according to project policy.

Exit criteria:

- All endurance acceptance criteria pass.
- Release is explicitly approved as production-ready.

---

## 31. Revision history

| Version | Date | Summary |
|---|---|---|
| 1.0 | 2026-07-13 | Initial production-grade AI-agent specification. |
| 1.1 | 2026-07-13 | Added normative requirement identifiers and traceability, froze the v1.0 public API/data models, defined formal session/transaction/reconnect/safe-enable/long-operation state machines, mandated a complete command-policy matrix, quantified runtime service targets, and added ADR/change-control rules. |

## 32. Definition of done

The task is complete only when:

- The package installs as a Python module from wheel and sdist.
- All stable public methods are typed, documented, and tested.
- SCPI and legacy protocols are implemented with bounded I/O.
- Every supplied command appears in the command-policy matrix.
- Every normative requirement is traceable to implementation and verification evidence.
- The frozen public API compatibility test passes.
- Session, transaction, reconnect, safe-enable, and long-operation state machines have complete transition coverage.
- Unsafe implicit behavior is absent.
- Retry and reconnect behavior cannot duplicate hazardous operations silently.
- All critical ambiguities are resolved or excluded from stable API.
- Windows and Ubuntu CI pass.
- Real-hardware validation passes.
- The 168-hour soak passes.
- Documentation and examples are complete.
- The release checklist contains no waived critical item.

Until Gate G8 passes, the project may be called an implementation candidate or release candidate, but not production-ready for unattended 24/7 use.
