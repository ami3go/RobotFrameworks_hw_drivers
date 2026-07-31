# RFDS-007 — Error and Exception Standard

**Version:** 1.0  
**Document ID:** RFDS-007  
**Status:** Project requirement  
**Applies to:** All RFDS Robot Framework driver packages, shared driver components, transport adapters, protocol parsers, simulators, and conformance tests

---

## 1. Purpose

This specification defines the mandatory error, exception, diagnostic, retry, recovery, and Robot Framework failure behavior for RFDS drivers.

The standard shall ensure that every failure:

1. is represented by a defined exception class;
2. has a stable machine-readable error code;
3. produces a deterministic and actionable Robot Framework failure message;
4. preserves the original technical cause;
5. includes sufficient structured diagnostic context;
6. does not expose credentials or other protected data;
7. declares whether retry or recovery is permitted;
8. leaves the driver in a documented state;
9. is testable through unit, integration, and RFDS conformance tests;
10. is described in the RFDS-017 AI Driver Contract.

The objective is to make driver failures consistent across instruments and transports while retaining enough detail for operators, test developers, CI systems, and AI agents to make correct decisions.

---

## 2. Scope

### 2.1 In scope

RFDS-007 covers:

- Python exception classes exposed by RFDS drivers;
- validation failures;
- configuration failures;
- connection and transport failures;
- protocol framing, parsing, and response failures;
- device-reported errors;
- driver state and precondition failures;
- resource conflicts;
- safety and interlock failures;
- dependency and internal-driver failures;
- timeout behavior;
- retry classification and retry evidence;
- uncertain or indeterminate command outcomes;
- exception chaining;
- cleanup failures;
- Robot Framework failure rendering;
- structured diagnostic records;
- logging and evidence requirements;
- redaction of sensitive information;
- error recovery and post-failure state;
- error catalogue requirements in RFDS-017;
- protocol-error and recovery verification under RFDS-019.

### 2.2 Out of scope

RFDS-007 does not define:

- the complete public keyword API;
- transport implementation architecture;
- package and repository layout except for error-related artifacts;
- physical device accuracy;
- general safety limits for a specific bench;
- end-user localization;
- vendor-specific command syntax;
- test-result business logic such as measurement PASS or FAIL when no driver error occurred.

A valid measurement that fails an engineering acceptance limit is a **test assertion failure**, not a driver exception, unless the driver itself could not perform or interpret the measurement.

---

## 3. Normative Terminology

- **shall / shall not** — mandatory requirement;
- **should / should not** — recommended requirement; deviations require documented justification;
- **may** — permitted implementation choice;
- **public boundary** — any Robot Framework keyword or documented public Python API;
- **diagnostic record** — structured machine-readable information describing one failure;
- **primary failure** — the error that caused the requested operation to fail;
- **secondary failure** — an error occurring during cleanup, rollback, disconnect, or diagnostic collection;
- **uncertain outcome** — the driver cannot prove whether a device-changing operation was executed.

---

## 4. Core Principles

### 4.1 Fail explicitly

A driver shall raise a defined exception when an operation cannot satisfy its documented postconditions.

A driver shall not silently convert an operational failure into:

- `None`;
- an empty string;
- zero;
- `False`;
- an empty list or dictionary;
- a fabricated default value;
- a logged warning followed by apparent success.

A sentinel return value may be used only when the public API explicitly defines it as a valid result and the distinction from failure is unambiguous.

### 4.2 Validate before side effects

Arguments, configuration, state preconditions, and safety limits shall be validated before device communication or other side effects whenever technically possible.

An invalid value that can be detected locally shall not be transmitted to the device merely to obtain a device error.

### 4.3 Preserve the cause

A driver shall preserve the original exception by Python exception chaining:

```python
raise DriverTimeoutError(...) from exc
```

The original cause shall remain available in logs and diagnostic evidence, but raw third-party exceptions shall not cross the public boundary unless the public API explicitly documents them.

### 4.4 Stable machine semantics

Automation shall make decisions using exception class, error code, retryability, and structured fields—not by parsing free-form message text.

Error codes and exception meanings shall remain backward compatible within a released major driver API.

### 4.5 Actionable operator output

A public failure message shall state:

1. what operation failed;
2. why it failed at the highest reliable level;
3. the most relevant context;
4. whether retry is allowed;
5. the immediate recovery action when known.

### 4.6 No hidden unlimited behavior

A driver shall not retry forever, wait indefinitely, reconnect indefinitely, or suppress repeated failures.

Every retry sequence shall have an explicit maximum attempt count or total time budget.

### 4.7 Safe post-failure state

Every error path shall define the resulting driver state and required recovery path. When the device state cannot be proven, the driver shall report an uncertain outcome rather than assume success or failure.

---

## 5. Mandatory Root Exception

Every RFDS driver shall expose one documented root exception named:

```python
DriverError
```

All public driver exceptions shall inherit from `DriverError`.

The root exception shall provide, directly or through equivalent properties:

```python
class DriverError(Exception):
    code: str
    message: str
    retryable: bool
    severity: str
    details: Mapping[str, object]
    recovery_action: str | None
    operation: str | None
    keyword: str | None
```

The implementation may add fields, but shall not remove the required semantics.

The root class shall support deterministic conversion to:

- a human-readable string;
- a Robot Framework failure string;
- a JSON-compatible diagnostic dictionary.

---

## 6. Mandatory Exception Hierarchy

Each driver shall implement or import the following canonical hierarchy. A driver may add subclasses where required by its protocol or device.

```text
DriverError
├── DriverConfigurationError
├── DriverValidationError
│   ├── DriverArgumentTypeError
│   ├── DriverArgumentValueError
│   ├── DriverRangeError
│   └── DriverUnsupportedValueError
├── DriverStateError
│   ├── DriverPreconditionError
│   └── DriverOperationUncertainError
├── DriverConnectionError
├── DriverTransportError
│   ├── DriverTransportOpenError
│   ├── DriverTransportClosedError
│   ├── DriverWriteError
│   ├── DriverReadError
│   └── DriverTimeoutError
├── DriverProtocolError
│   ├── DriverMalformedResponseError
│   ├── DriverIncompleteResponseError
│   ├── DriverUnexpectedResponseError
│   ├── DriverChecksumError
│   └── DriverProtocolSyncError
├── DriverDeviceError
│   ├── DriverCommandRejectedError
│   ├── DriverDeviceBusyError
│   ├── DriverIdentityError
│   └── DriverUnsupportedOperationError
├── DriverResourceError
│   ├── DriverResourceNotFoundError
│   ├── DriverResourceBusyError
│   └── DriverResourceConflictError
├── DriverSafetyError
│   ├── DriverUnsafeOperationError
│   ├── DriverInterlockError
│   └── DriverLimitViolationError
├── DriverDependencyError
└── DriverInternalError
```

### 6.1 Hierarchy rules

1. Canonical classes shall retain the meanings defined in this document.
2. A more specific class shall be used when the failure can be classified reliably.
3. `DriverInternalError` shall be the last-resort wrapper for an unexpected implementation defect, not a substitute for classification.
4. Driver-specific exceptions shall inherit from the nearest canonical parent.
5. Public code shall be able to catch `DriverError` to handle all driver failures.
6. Public exception names shall not shadow Python built-ins such as `ConnectionError`, `TimeoutError`, or `ValueError` without the `Driver` prefix.

---

## 7. Exception Classification

### 7.1 Configuration errors

Use `DriverConfigurationError` when static or startup configuration is missing, invalid, incompatible, or unsupported.

Examples:

- invalid resource string format;
- missing required serial setting;
- unsupported transport selection;
- incompatible options;
- invalid configuration file schema.

### 7.2 Validation errors

Use `DriverValidationError` or a subclass when the caller supplied an invalid argument and the failure is detected before transport execution.

Examples:

- wrong type;
- out-of-range voltage;
- unknown mode;
- mutually exclusive arguments;
- invalid channel number.

Validation failures shall normally be non-retryable until input changes.

### 7.3 State errors

Use `DriverStateError` when the operation is valid in general but not valid in the current driver or device state.

Examples:

- measurement requested while disconnected;
- configuration changed while acquisition is running;
- close requested during a protected critical section;
- operation requires remote mode.

### 7.4 Connection and transport errors

Use connection and transport exceptions for failures below the device-protocol semantic layer.

Examples:

- resource cannot be opened;
- socket disconnected;
- serial write failed;
- VISA read failed;
- read timeout;
- transport closed unexpectedly.

### 7.5 Protocol errors

Use protocol exceptions when bytes or messages were exchanged but did not satisfy the protocol contract.

Examples:

- malformed SCPI response;
- incomplete binary frame;
- checksum mismatch;
- unexpected response type;
- protocol stream cannot be resynchronized.

### 7.6 Device errors

Use device exceptions when the device communicated successfully but rejected or could not execute the requested operation.

Examples:

- device error queue reports an error;
- command not supported by the model;
- device busy;
- identity does not match the required model;
- command rejected due to device-local state.

### 7.7 Safety errors

Use safety exceptions when an operation is blocked because it violates a driver, device, fixture, or bench safety rule.

Safety exceptions shall be raised before transmitting a prohibited command whenever possible.

### 7.8 Resource errors

Use resource exceptions for missing, busy, conflicting, or exclusively held resources such as ports, sessions, channels, locks, fixtures, or relay paths.

### 7.9 Dependency errors

Use `DriverDependencyError` when a required package, runtime, shared library, SDK, firmware capability, or compatible version is unavailable.

### 7.10 Internal errors

Use `DriverInternalError` only for unexpected defects or violated internal invariants.

Its public message shall be controlled and shall not expose internal secrets. Full traceback evidence shall be retained for developers.

---

## 8. Error Code Standard

### 8.1 Format

Canonical RFDS error codes shall use:

```text
RFDS-<DOMAIN>-<NNN>
```

Where:

- `RFDS` is the fixed prefix;
- `<DOMAIN>` is a three-character uppercase domain;
- `<NNN>` is a zero-padded decimal identifier from `001` to `999`.

Examples:

```text
RFDS-ARG-002
RFDS-TMO-001
RFDS-PRT-003
RFDS-SAF-001
```

### 8.2 Canonical domains

| Domain | Meaning |
|---|---|
| `CFG` | Configuration |
| `ARG` | Argument and local validation |
| `STA` | Driver or device state |
| `CON` | Connection lifecycle |
| `TRN` | Transport I/O |
| `TMO` | Timeout |
| `PRT` | Protocol framing, parsing, or schema |
| `DEV` | Device-reported or device-semantic error |
| `RES` | Shared or exclusive resource |
| `SAF` | Safety, limit, or interlock |
| `DEP` | Dependency or compatibility |
| `INT` | Unexpected internal failure |

### 8.3 Driver-specific codes

A device-specific extension shall use:

```text
RFDS-<DRIVER_SHORT_ID>-<NNN>
```

The driver short identifier shall be documented in the driver error catalogue and shall not conflict with canonical domains.

Example:

```text
RFDS-N6700-101
```

### 8.4 Stability rules

1. An error code shall have one stable semantic meaning.
2. A released code shall not be reassigned.
3. Message wording may improve without changing the code when semantics remain unchanged.
4. A semantic change requires a new code.
5. Deprecated codes shall remain reserved.
6. The code shall appear in every public failure string and diagnostic record.

---

## 9. Canonical Error Code Catalogue

The following minimum code set shall be supported where applicable.

| Code | Canonical exception | Meaning | Default retryable |
|---|---|---|---:|
| `RFDS-CFG-001` | `DriverConfigurationError` | Missing required configuration | No |
| `RFDS-CFG-002` | `DriverConfigurationError` | Invalid configuration value or schema | No |
| `RFDS-CFG-003` | `DriverConfigurationError` | Unsupported configuration combination | No |
| `RFDS-ARG-001` | `DriverArgumentTypeError` | Invalid argument type | No |
| `RFDS-ARG-002` | `DriverArgumentValueError` | Invalid argument value | No |
| `RFDS-ARG-003` | `DriverRangeError` | Value outside supported range | No |
| `RFDS-ARG-004` | `DriverUnsupportedValueError` | Unsupported enum, mode, or option | No |
| `RFDS-ARG-005` | `DriverValidationError` | Conflicting or incomplete arguments | No |
| `RFDS-STA-001` | `DriverPreconditionError` | Operation precondition not satisfied | Conditional |
| `RFDS-STA-002` | `DriverStateError` | Operation invalid in current state | Conditional |
| `RFDS-STA-003` | `DriverOperationUncertainError` | Device-changing operation may or may not have executed | No automatic retry |
| `RFDS-CON-001` | `DriverTransportOpenError` | Connection or session open failed | Conditional |
| `RFDS-CON-002` | `DriverConnectionError` | Driver is not connected | Conditional |
| `RFDS-CON-003` | `DriverConnectionError` | Connection lost | Conditional |
| `RFDS-CON-004` | `DriverConnectionError` | Identity or handshake failed during connection | Conditional |
| `RFDS-TRN-001` | `DriverWriteError` | Transport write failed | Conditional |
| `RFDS-TRN-002` | `DriverReadError` | Transport read failed | Conditional |
| `RFDS-TRN-003` | `DriverTransportClosedError` | Transport is closed | Conditional |
| `RFDS-TRN-004` | `DriverTransportError` | Transport framing or low-level I/O failure | Conditional |
| `RFDS-TMO-001` | `DriverTimeoutError` | Operation exceeded its timeout | Conditional |
| `RFDS-PRT-001` | `DriverMalformedResponseError` | Response format is malformed | Conditional |
| `RFDS-PRT-002` | `DriverIncompleteResponseError` | Response or frame is incomplete | Conditional |
| `RFDS-PRT-003` | `DriverUnexpectedResponseError` | Response type or content is unexpected | Conditional |
| `RFDS-PRT-004` | `DriverChecksumError` | Checksum or integrity validation failed | Conditional |
| `RFDS-PRT-005` | `DriverProtocolSyncError` | Protocol stream synchronization was lost | Conditional |
| `RFDS-DEV-001` | `DriverCommandRejectedError` | Device rejected a command | No unless documented |
| `RFDS-DEV-002` | `DriverDeviceError` | Device error queue or status reports failure | No unless documented |
| `RFDS-DEV-003` | `DriverDeviceBusyError` | Device is temporarily busy | Yes when documented |
| `RFDS-DEV-004` | `DriverUnsupportedOperationError` | Device or model does not support operation | No |
| `RFDS-DEV-005` | `DriverIdentityError` | Connected device identity is not accepted | No |
| `RFDS-RES-001` | `DriverResourceNotFoundError` | Required resource was not found | Conditional |
| `RFDS-RES-002` | `DriverResourceBusyError` | Resource is already in use | Yes when release is expected |
| `RFDS-RES-003` | `DriverResourceConflictError` | Resource allocation conflicts with another operation | No until plan changes |
| `RFDS-SAF-001` | `DriverUnsafeOperationError` | Operation is prohibited by a safety rule | No |
| `RFDS-SAF-002` | `DriverInterlockError` | Required safety interlock is not satisfied | No until condition changes |
| `RFDS-SAF-003` | `DriverLimitViolationError` | Requested operation exceeds a configured safety limit | No |
| `RFDS-DEP-001` | `DriverDependencyError` | Required dependency is missing | No |
| `RFDS-DEP-002` | `DriverDependencyError` | Dependency, SDK, firmware, or runtime version is incompatible | No |
| `RFDS-INT-001` | `DriverInternalError` | Internal invariant failed | No |
| `RFDS-INT-002` | `DriverInternalError` | Unexpected unclassified implementation failure | No |

“Conditional” means retryability shall be decided using operation semantics, delivery state, and documented recovery policy.

---

## 10. Mandatory Exception Data

Every raised public `DriverError` shall contain:

| Field | Requirement |
|---|---|
| `code` | Stable error code defined by this specification or the driver catalogue |
| `message` | Concise human-readable explanation |
| `retryable` | Explicit Boolean; never inferred from text |
| `severity` | `ERROR` or `CRITICAL` for raised public exceptions |
| `operation` | Python operation or protocol operation when known |
| `keyword` | Robot Framework keyword when known |
| `details` | JSON-compatible context dictionary |
| `recovery_action` | Immediate recovery instruction when known, otherwise null |

The following fields should be present when applicable:

- driver name and version;
- transport type;
- resource identifier;
- channel or endpoint;
- timeout;
- attempt number and maximum attempts;
- state before and after failure;
- raw vendor error code;
- command or query summary;
- response summary;
- device identity;
- correlation identifier;
- evidence reference.

Unknown values shall be omitted or set to null. They shall not be fabricated.

---

## 11. Public Failure Message Format

The canonical Robot Framework and public Python message format shall be:

```text
[<ERROR_CODE>] <operation> failed: <reason>. <key context>. Retryable=<yes|no>. Recovery=<action|none>.
```

Example:

```text
[RFDS-TMO-001] Get DC Voltage failed: no complete SCPI response was received within 5.000 s. Transport=VISA; Resource=TCPIP0::192.168.0.55::INSTR; Attempt=2/2. Retryable=yes. Recovery=verify the connection and repeat the query.
```

### 11.1 Message rules

1. The error code shall be first.
2. The operation or keyword shall be named.
3. The reason shall be specific but concise.
4. Units shall be included for numeric timing and limits.
5. The message shall not contain a Python traceback.
6. The message shall not contain credentials, tokens, full secret-bearing URLs, or unredacted protected payloads.
7. Raw binary data shall not be placed in the public message.
8. Volatile details shall be placed after the stable reason or in structured diagnostics.
9. Driver messages shall be in English unless a project-wide localization standard is introduced.
10. Tests shall assert the code and structured fields; exact full-message matching should be limited to stable fragments.

---

## 12. Robot Framework Behavior

### 12.1 Keyword failure

A public Robot Framework keyword shall fail by raising a `DriverError` or a subclass. Robot Framework shall receive the canonical public failure message.

A keyword shall not both return a success value and report a driver failure.

### 12.2 Assertion failures versus driver errors

Driver keywords that explicitly implement assertions, such as `Voltage Should Be Within Limits`, may raise Robot Framework assertion failures when:

- communication succeeded;
- data was valid;
- the measured value did not meet the assertion.

Communication, parsing, safety, configuration, or state failures shall remain driver exceptions and shall not be mislabeled as ordinary assertion failures.

### 12.3 Fatal failures

Robot Framework fatal errors shall be used only when continuing the suite is unsafe or structurally impossible, such as:

- required emergency shutdown failed;
- the shared driver process is corrupted;
- continuing could cause unsafe device behavior;
- suite-wide setup cannot establish a mandatory resource and the suite explicitly requires fatal behavior.

A normal timeout or one failed keyword shall not automatically become a fatal suite failure.

### 12.4 Return values

When a keyword fails, it shall not return a partial result unless the API explicitly defines a typed result that contains both partial data and a failure status. Even then, transport and safety failures shall normally raise exceptions.

---

## 13. Validation and Transmission Rules

1. Local validation shall occur before I/O.
2. A locally rejected operation shall produce no outbound protocol traffic.
3. Validation evidence should identify the rejected field, received value, and allowed constraint.
4. Error messages shall not expose an entire large payload when one field caused the failure.
5. Floating-point range diagnostics shall state the unit and inclusive/exclusive boundaries.
6. Enum diagnostics shall list supported values when the list is reasonably small and non-sensitive.
7. Conflicting arguments shall identify the conflicting fields.
8. A driver shall not depend solely on vendor error responses for basic local validation.

Example:

```text
[RFDS-ARG-003] Set Current failed: requested current 12.0 A exceeds the configured maximum of 10.0 A. Channel=1. Retryable=no. Recovery=reduce the requested current or revise the approved safety limit.
```

---

## 14. Timeout Standard

### 14.1 Explicit timeouts

Every potentially blocking transport or device operation shall have a finite timeout derived from:

- a documented keyword argument;
- driver configuration;
- transport configuration;
- a documented default.

An unbounded blocking call is prohibited.

### 14.2 Timeout diagnostics

A timeout error shall include:

- timeout duration;
- operation type;
- whether any bytes or acknowledgement were received;
- attempt count;
- whether the operation is safe to retry;
- resulting connection state;
- recovery action.

### 14.3 Timeout classification

A timeout while waiting for a read-only query may be retryable.

A timeout after transmission of a device-changing command shall not be automatically retried unless the driver can prove idempotency or prove that the command was not delivered.

When execution status cannot be determined, the driver shall raise:

```text
DriverOperationUncertainError
RFDS-STA-003
```

The driver shall require read-back, state reconciliation, reset, or operator confirmation before another state-changing operation when necessary.

---

## 15. Retry Standard

### 15.1 General rules

A retry policy shall be explicit, bounded, observable, and operation-aware.

Each retry sequence shall define:

- retryable exception classes or codes;
- idempotency requirement;
- maximum attempts;
- delay or backoff policy;
- total time budget when applicable;
- reconnection behavior;
- final exception behavior.

### 15.2 Prohibited automatic retries

The driver shall not automatically retry:

- invalid arguments;
- unsupported operations;
- safety violations;
- interlock violations;
- identity mismatch;
- incompatible configuration;
- non-idempotent commands with uncertain delivery;
- device command rejection unless the device documentation defines a transient condition;
- internal invariant failures.

### 15.3 Retry evidence

Every retry attempt shall be visible in structured logs and shall include:

- attempt number;
- triggering error code;
- delay before retry;
- whether reconnection occurred;
- final outcome.

Intermediate retries should be logged as `WARNING`. The final failure shall be logged once as `ERROR` or `CRITICAL`.

### 15.4 No duplicate side effects

Before retrying a state-changing operation, the driver shall determine one of:

1. the operation was not transmitted;
2. the operation is idempotent;
3. the device state was read back and reconciled;
4. the protocol provides a transaction identifier or deduplication mechanism.

Otherwise the outcome is uncertain and automatic retry is prohibited.

---

## 16. Recovery and Driver State

### 16.1 Required state declaration

Each exception path shall define the driver state after failure using the canonical session-state enum owned by RFDS-003 §13.1 (`DISCONNECTED`, `CONNECTING`, `CONNECTED`, `CONFIGURED`, `BUSY`, `WAITING`, `RECOVERING`, `ERROR`, `CLOSING`). The driver's RFDS-017 contract shall reference this same enum rather than defining a competing one.

A state-changing exception that leaves the device in a condition requiring reconciliation before further use shall report `ERROR` or `RECOVERING` as applicable, with the recovery classification (Section 16.2) supplying the finer-grained detail RFDS-003's enum does not itself capture.

### 16.2 Recovery classifications

Each error catalogue entry shall classify recovery as one of:

- `NONE_REQUIRED` — the next operation may proceed;
- `RETRY_ALLOWED` — the same operation may be retried under policy;
- `RECONNECT_REQUIRED` — transport must be re-established;
- `RESYNC_REQUIRED` — protocol stream must be cleared or synchronized;
- `READBACK_REQUIRED` — device state must be queried before continuation;
- `RESET_REQUIRED` — device or driver reset is required;
- `OPERATOR_ACTION_REQUIRED` — physical or administrative action is required;
- `EMERGENCY_SHUTDOWN_REQUIRED` — immediate safe shutdown is required;
- `NOT_RECOVERABLE` — current session or process cannot continue safely.

### 16.3 Recovery verification

When a failure is documented as recoverable, tests shall perform the documented recovery and then execute a known-good keyword.

A driver shall not claim recovery merely because no exception was raised by the cleanup function.

### 16.4 State reconciliation

After uncertain state-changing failures, the driver shall use available read-back, status, error queue, identity, or connection checks to reconcile state.

If reconciliation is impossible, the session shall remain `RECOVERY_REQUIRED` or equivalent.

---

## 17. Exception Translation at Layer Boundaries

Each software layer shall translate only the errors it owns and shall preserve the cause.

Recommended mapping:

```text
Operating system / SDK / PyVISA / pyserial / socket exception
        ↓
Transport-specific internal exception
        ↓
Canonical DriverTransportError / DriverTimeoutError
        ↓
Protocol parser exception, when applicable
        ↓
Canonical DriverProtocolError
        ↓
Public Robot Framework failure message + diagnostic record
```

### 17.1 Translation rules

1. Vendor-specific error codes shall be retained in `details.vendor_code` when available.
2. Raw vendor exception text may be retained in developer diagnostics after redaction.
3. Public code shall receive canonical exception types.
4. Translation shall not erase whether the failure occurred during open, write, read, parse, close, or recovery.
5. A layer shall not repeatedly wrap an already canonical exception unless adding essential semantic context.
6. Re-raising a canonical exception shall preserve the original code unless the semantic category genuinely changes.

---

## 18. Cleanup, Rollback, and Multiple Failures

### 18.1 Primary failure preservation

A cleanup or disconnect failure shall not replace the primary operation failure.

The primary exception shall remain the raised exception. Secondary failures shall be recorded in:

```text
details.secondary_errors
```

or an equivalent structured field.

### 18.2 Rollback

When a state-changing operation partially completes, the driver may attempt rollback only when rollback is documented and safe.

Rollback failure shall be recorded and may elevate severity to `CRITICAL` if the device cannot be returned to a safe or known state.

### 18.3 Close behavior

A close or disconnect keyword shall be idempotent unless the device protocol makes this impossible.

Calling close on an already closed session should normally succeed without error. A driver shall document any different behavior.

### 18.4 Emergency actions

Emergency shutdown and safe-state operations shall prioritize safety over preservation of normal session state. Any failure during emergency action shall be recorded as `CRITICAL` and shall clearly state the remaining uncertainty.

---

## 19. Structured Diagnostic Record

Every public driver failure shall be convertible to a JSON-compatible record with at least:

```yaml
schema_version: "1.0"
timestamp_utc: "2026-07-26T12:34:56.789Z"
error_id: "uuid-or-equivalent"
code: "RFDS-TMO-001"
exception_type: "DriverTimeoutError"
message: "No complete response was received within the configured timeout."
severity: "ERROR"
retryable: true
recovery_class: "RETRY_ALLOWED"
recovery_action: "Verify connection and repeat the query."
driver:
  name: "rf_example"
  version: "26.01"
keyword: "Get Identity"
operation: "query"
state_before: "CONNECTED"
state_after: "CONNECTED"
transport:
  type: "SCPI_TCP"
  resource: "192.168.0.55:5025"
protocol:
  request_summary: "*IDN?"
  response_summary: null
  bytes_received: 0
timeout_s: 5.0
attempt: 2
max_attempts: 2
cause:
  type: "TimeoutError"
  vendor_code: null
correlation_id: "run-or-keyword-correlation-id"
evidence:
  - "outbound_trace.log#entry-0042"
secondary_errors: []
redactions_applied: []
```

### 19.1 Diagnostic rules

1. Timestamps shall use UTC and ISO 8601.
2. Records shall be JSON serializable.
3. Unknown fields shall be null or omitted.
4. Raw payloads shall be stored only when permitted and size-bounded.
5. Large binary data shall be referenced as evidence, not embedded.
6. Diagnostic collection failure shall not replace the primary exception.
7. Correlation identifiers shall allow association with Robot Framework test, keyword, protocol vector, and transport trace.

---

## 20. Logging Standard

### 20.1 Levels

| Level | Use |
|---|---|
| `TRACE` | Raw protocol bytes and other trace-level detail (see RFDS-008 §28.1) |
| `DEBUG` | Detailed state transitions, sanitized protocol traces, parser details |
| `INFO` | Connection lifecycle, identity, configuration summary, successful recovery |
| `WARN` | Retry attempt, transient anomaly, recoverable degradation |
| `ERROR` | Final failed public operation |
| `CRITICAL` | Unsafe, unrecoverable, corrupted, or emergency-shutdown failure |

RFDS-008 §28.1 is the sole normative source for the platform's logging-level set and their evidence-level meaning; this table uses RFDS-008's level names (`WARN`, not `WARNING`) for exception- and error-related logging specifically.

### 20.2 One-owner logging

The layer that converts a failure into the final public exception shall log the final failure once.

Lower layers may log `DEBUG` context but shall not produce repeated `ERROR` entries for the same propagated exception.

### 20.3 Required log fields

Structured logs shall include when available:

- timestamp;
- level;
- error code;
- exception type;
- driver name and version;
- Robot Framework suite, test, and keyword;
- operation;
- transport and resource;
- retry attempt;
- correlation identifier;
- state before and after;
- recovery classification.

### 20.4 Tracebacks

Full Python tracebacks shall be available in developer diagnostics for `DriverInternalError` and unexpected causes.

Tracebacks should not be shown in routine operator output unless verbose or debug mode is explicitly enabled.

### 20.5 Relationship to RFDS-008

The §19 diagnostic record is the canonical representation of one raised exception. When persisted as run evidence, it shall be carried into the RFDS-008 §17 error-evidence record without renaming fields that already have an RFDS-007 name (`code`, `exception_type`, `message`, `retryable`, `recovery_class`/`recovery_action`, `correlation_id`); RFDS-008 adds the surrounding run/session/sequence identifiers and storage rules. RFDS-008 is the sole normative source for how error evidence is stored, correlated, and redacted at the run level.

---

## 21. Sensitive Data and Redaction

### 21.1 Data that shall be redacted

Drivers shall redact:

- passwords;
- API tokens;
- authentication headers;
- private keys;
- session cookies;
- secret query parameters;
- protected calibration or customer data when classified as sensitive;
- full user credentials embedded in resource strings;
- device data defined as confidential by the project.

### 21.2 Redaction form

Redacted data shall use a visible marker such as:

```text
<redacted>
```

A diagnostic record should identify which fields were redacted without revealing their values. This inline text marker is for human-readable log output; the structured JSON redaction marker used in machine-readable evidence (`{"value": "<REDACTED>", "redacted": true, "reason": "..."}`) is governed by RFDS-008 §29.3.

### 21.3 Protocol evidence

Protocol traces may retain non-secret commands and responses required for conformance evidence. Secrets shall be removed before evidence is stored or published.

### 21.4 No over-redaction

Redaction shall not remove essential non-sensitive diagnostic information such as:

- transport type;
- host without credentials;
- port;
- command header;
- error code;
- channel;
- timeout;
- response length.

---

## 22. Error Catalogue Artifact

Each driver package shall provide, directly or through equivalent generated documentation:

```text
rf_<driver_name>/
├── errors.py
├── diagnostics.py
├── docs/
│   └── error_reference.md
├── ai/
│   └── ai_contract.yaml
└── tests/
    ├── unit/
    └── conformance/
```

The driver error catalogue shall contain for every public error:

- code;
- exception class;
- title;
- meaning;
- trigger conditions;
- affected keywords;
- retryable Boolean or rule;
- recovery classification;
- required recovery action;
- post-failure driver state;
- whether device state may be uncertain;
- operator message template;
- structured fields;
- test references;
- first driver version containing the error;
- deprecation status.

No public error shall exist only in source code without catalogue coverage.

---

## 23. RFDS-017 Integration

The RFDS-017 AI Driver Contract shall include an error catalogue consistent with this specification.

For each capability or keyword, RFDS-017 shall identify:

- applicable error codes;
- exception classes;
- precondition failures;
- transport and protocol failures;
- timeout behavior;
- retry policy;
- recovery class;
- post-failure state;
- uncertain outcome behavior;
- safety-related failures.

An AI agent shall be able to determine from RFDS-017 whether it may retry, reconnect, read back state, ask for operator action, or abort the test.

`UNKNOWN` shall be used when the driver contract cannot reliably classify a device-specific outcome. `UNKNOWN` shall not be silently converted into retryable behavior.

---

## 24. RFDS-018 Integration

RFDS-018 may impose bench-wide error and recovery rules that are stricter than a single driver policy.

Examples:

- a PSU timeout requires relay isolation before reconnection;
- a DMM failure permits substitution by a preferred alternate meter;
- an interlock failure requires operator acknowledgement;
- a shared VISA resource conflict prevents parallel execution;
- a bench emergency requires a defined multi-driver shutdown sequence.

When driver and bench recovery rules differ, the safer and more restrictive applicable rule shall govern.

Bench-level orchestration shall preserve the original driver error code while adding bench correlation and recovery evidence.

---

## 25. RFDS-019 Conformance Integration

RFDS-019 protocol conformance tests shall verify applicable RFDS-007 behavior, including:

- timeout exception class and code;
- malformed and incomplete response handling;
- device error handling;
- transport disconnect handling;
- command-only no-response behavior;
- recovery after documented recoverable failures;
- no automatic retry of uncertain state-changing operations;
- correct Robot Framework failure rendering;
- traceable protocol and diagnostic evidence.

A protocol failure shall not pass merely because the keyword raised an exception. The exception class, code, retryability, post-failure state, and recovery behavior shall match the declared contract.

---

## 26. Testing Requirements

### 26.1 Unit tests

Unit tests shall verify:

- each canonical exception can be constructed;
- required fields are present;
- `str(exception)` is deterministic;
- diagnostic serialization is valid JSON;
- cause chaining is preserved;
- sensitive values are redacted;
- public messages contain the error code;
- driver-specific subclasses inherit from the correct canonical class;
- error codes are unique;
- deprecated codes are not reused.

### 26.2 Keyword tests

For each public keyword, tests shall cover applicable failures:

- invalid type;
- invalid range or enum;
- disconnected state;
- transport write failure;
- timeout;
- malformed response;
- device rejection;
- safety rejection;
- recovery or non-recovery path.

### 26.3 Protocol-boundary tests

Tests shall prove:

- local validation failures transmit no command;
- retry count matches policy;
- no duplicate state-changing command occurs after uncertain delivery;
- post-failure known-good communication succeeds when recovery is declared;
- protocol evidence is linked to the diagnostic record.

### 26.4 Cleanup tests

Tests shall verify that:

- secondary cleanup errors do not mask the primary error;
- disconnect is idempotent where required;
- rollback failures are retained;
- emergency action failures produce `CRITICAL` evidence.

### 26.5 Robot Framework tests

Robot Framework tests shall verify:

- the keyword fails with the declared code;
- the failure text is actionable;
- the result is not misreported as PASS;
- retry and recovery keywords behave as documented;
- failure diagnostics are present in generated evidence.

---

## 27. Acceptance Criteria

A driver conforms to RFDS-007 only when:

1. all public driver exceptions inherit from `DriverError`;
2. the canonical hierarchy is implemented or imported;
3. every public error has a stable unique code;
4. every raised public exception contains the mandatory data;
5. all public failure messages begin with the error code;
6. invalid locally detectable input is rejected before I/O;
7. raw third-party exceptions do not leak through the public boundary;
8. original causes are preserved by exception chaining;
9. all potentially blocking operations have finite timeouts;
10. retry behavior is explicit, bounded, and idempotency-aware;
11. uncertain state-changing outcomes use `RFDS-STA-003` or an approved subclass;
12. cleanup failures do not mask the primary failure;
13. post-failure state and recovery class are documented;
14. structured diagnostics are JSON serializable;
15. secrets are redacted from messages, logs, and evidence;
16. RFDS-017 lists applicable errors per capability;
17. RFDS-019 verifies applicable protocol errors and recovery;
18. no mandatory error test remains NOT RUN without approved justification;
19. documentation and examples use the same error codes and class names as the implementation;
20. no Critical or Major error-handling review finding remains unresolved at release.

---

## 28. Failure Conditions

RFDS-007 conformance shall fail when:

- a driver returns apparent success after an operational failure;
- a public exception lacks an error code;
- the same code has multiple meanings;
- a released code is reused;
- a raw vendor or built-in exception reaches Robot Framework unexpectedly;
- a timeout can block indefinitely;
- retry is unlimited or hidden;
- a non-idempotent uncertain command is automatically repeated;
- an invalid local argument is transmitted unnecessarily;
- a cleanup exception replaces the primary exception;
- the public message exposes a secret;
- the driver logs a failure but returns success;
- a recoverable error has no tested recovery path;
- an unrecoverable error is marked retryable;
- post-failure state is undefined;
- RFDS-017 error metadata contradicts implementation;
- RFDS-019 expected error behavior contradicts implementation;
- error evidence cannot be correlated with the keyword and protocol operation.

---

## 29. Review Checklist

1. Is there one documented `DriverError` root class?
2. Do all public exceptions inherit from it?
3. Are built-in exception names avoided at the public boundary?
4. Does every public error have a stable unique code?
5. Are all codes present in the error catalogue?
6. Are messages deterministic, concise, and actionable?
7. Are required structured fields present?
8. Are original causes preserved?
9. Are validation failures detected before I/O?
10. Are timeouts finite and documented?
11. Is retry bounded and safe for the operation?
12. Is uncertain command delivery represented explicitly?
13. Does every failure define the post-failure state?
14. Is recovery classified and tested?
15. Are secondary cleanup failures retained without masking the primary failure?
16. Are secrets redacted from all output surfaces?
17. Are logs free from duplicate final error entries?
18. Are Robot Framework assertion failures separated from driver exceptions?
19. Does RFDS-017 list the applicable errors per keyword?
20. Does RFDS-019 test protocol failures and recovery at the device boundary?
21. Are documentation, examples, tests, and implementation consistent?
22. Are all Critical and Major review findings resolved?

---

## 30. Minimum Definition of Done

RFDS-007 implementation is complete for a driver when:

- the root exception and canonical hierarchy exist;
- the error-code catalogue is complete;
- all public keywords declare their applicable errors;
- structured diagnostics are generated;
- Robot Framework receives canonical failure messages;
- timeout, retry, uncertain-state, and recovery behavior are implemented;
- redaction is implemented and tested;
- unit and Robot Framework error tests pass;
- RFDS-019 protocol error and recovery vectors pass where applicable;
- RFDS-017 and user documentation are updated;
- error-handling review finds no unresolved Critical or Major issue.

---

## 31. Reference Implementation Pattern

The following pattern is informative. Equivalent implementations are permitted when all normative requirements are met.

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(eq=False)
class DriverError(Exception):
    code: str
    message: str
    retryable: bool = False
    severity: str = "ERROR"
    details: Mapping[str, Any] = field(default_factory=dict)
    recovery_action: str | None = None
    operation: str | None = None
    keyword: str | None = None

    def __post_init__(self) -> None:
        super().__init__(self.message)

    def __str__(self) -> str:
        operation = self.keyword or self.operation or "Driver operation"
        retry = "yes" if self.retryable else "no"
        recovery = self.recovery_action or "none"
        return (
            f"[{self.code}] {operation} failed: {self.message}. "
            f"Retryable={retry}. Recovery={recovery}."
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "exception_type": type(self).__name__,
            "message": self.message,
            "retryable": self.retryable,
            "severity": self.severity,
            "details": dict(self.details),
            "recovery_action": self.recovery_action,
            "operation": self.operation,
            "keyword": self.keyword,
        }


class DriverTimeoutError(DriverError):
    pass


def query_identity(transport: Any, timeout_s: float) -> str:
    try:
        return transport.query("*IDN?", timeout=timeout_s)
    except TimeoutError as exc:
        raise DriverTimeoutError(
            code="RFDS-TMO-001",
            message=f"no complete identity response was received within {timeout_s:.3f} s",
            retryable=True,
            recovery_action="verify the connection and repeat the query",
            operation="query_identity",
            keyword="Get Identity",
            details={"timeout_s": timeout_s, "request": "*IDN?"},
        ) from exc
```

The reference pattern does not replace the required driver-specific error catalogue, state handling, redaction, logging, and tests.

---

## 32. Goal

Provide one unified and machine-verifiable failure model for every RFDS Robot Framework driver so that operators, test suites, CI systems, and AI agents can distinguish invalid input, transport failure, protocol failure, device rejection, unsafe operation, uncertain state, recoverable failure, and internal defect without inspecting driver source code.

---

## Appendix A — Error Handling Decision Matrix

| Situation | Required exception | Retry rule | Required next action |
|---|---|---|---|
| Invalid local argument | `DriverValidationError` subclass | Do not retry unchanged | Correct input |
| Not connected | `DriverConnectionError` or `DriverPreconditionError` | Retry only after connect | Establish connection |
| Query timeout, no side effect | `DriverTimeoutError` | May retry under bounded policy | Retry or reconnect |
| State-changing command timeout, delivery unknown | `DriverOperationUncertainError` | No automatic retry | Read back, reconcile, reset, or operator action |
| Malformed response | `DriverProtocolError` subclass | Retry only if stream remains valid or after resync | Resynchronize or reconnect |
| Device reports busy | `DriverDeviceBusyError` | May retry when documented | Delay and retry within budget |
| Device rejects unsupported command | `DriverUnsupportedOperationError` | Do not retry | Change operation or device |
| Safety limit exceeded | `DriverLimitViolationError` | Do not retry unchanged | Reduce request or revise approved limit |
| Resource busy | `DriverResourceBusyError` | May retry when release is expected | Wait, release, or reschedule |
| Identity mismatch | `DriverIdentityError` | Do not retry blindly | Connect correct device or change profile |
| Internal invariant failure | `DriverInternalError` | Do not retry automatically | Abort session and review evidence |
| Cleanup fails after primary error | Preserve primary; record secondary | Depends on primary | Follow primary recovery plus cleanup remediation |

---

## Appendix B — Driver-Specific Error Catalogue Template

```yaml
schema_version: "1.0"
driver: "rf_example"
driver_version: "26.01"
errors:
  - code: "RFDS-DEV-001"
    exception: "DriverCommandRejectedError"
    title: "Device rejected command"
    meaning: "The device accepted communication but rejected the requested command."
    triggers:
      - "SCPI error queue returns a non-zero command error"
    keywords:
      - "Set DC Voltage"
    retryable: false
    recovery_class: "NONE_REQUIRED"
    recovery_action: "Correct the command arguments and repeat the operation."
    state_after: "CONNECTED"
    uncertain_device_state: false
    message_template: "Device rejected {command_summary}: {device_error}."
    required_details:
      - "device_error_code"
      - "command_summary"
    tests:
      - "ERR-DEV-001"
      - "RFDS019-VECTOR-SET-VOLTAGE-DEVICE-ERROR"
    introduced_in: "26.01"
    deprecated: false
```

---

## Appendix C — Change Control

Whenever a public keyword, transport operation, device error, timeout policy, retry policy, recovery action, or safety rule changes, the same driver revision shall update:

- exception classes;
- error codes and catalogue;
- RFDS-017 capability errors;
- RFDS-019 protocol error vectors;
- unit and Robot Framework tests;
- examples;
- user documentation;
- `history/` change description;
- `review/` code and conformance review.

A public failure-behavior change without corresponding documentation and tests shall fail release review.
