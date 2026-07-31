# RFDS-004 — Transport Layer Specification

**Version:** 1.0  
**Document ID:** RFDS-004  
**Status:** Draft project requirement  
**Applies to:** All RFDS Robot Framework driver packages that communicate through VISA, serial, raw TCP/IP, or direct USB

---

## 1. Purpose

This specification defines the mandatory transport abstraction used by RFDS Robot Framework drivers.

The transport layer shall provide a deterministic, testable, and backend-independent path between a device protocol implementation and a physical or simulated communication endpoint:

```text
Robot Framework keyword
        ↓
Driver public API
        ↓
Device protocol layer
        ↓
RFDS transport interface
        ↓
VISA / Serial / TCP/IP / USB backend
        ↓
Physical device or approved simulator
```

The specification standardizes:

- transport lifecycle and state;
- common byte-oriented read, write, and transaction operations;
- transport configuration and validation;
- timeout, cancellation, retry, and recovery behavior;
- text encoding, terminators, framing, and binary data handling;
- thread safety and transaction serialization;
- resource discovery and stable device selection;
- transport error classification;
- protocol trace observation required by conformance testing;
- backend-specific requirements for VISA, serial, TCP/IP, and USB;
- simulator and transport-spy behavior;
- package layout, tests, documentation, and acceptance criteria.

The goal is to allow the same device protocol code to operate over any supported transport without importing or directly depending on a specific transport library.

---

## 2. Scope Boundary

### 2.1 In scope

RFDS-004 covers:

- the internal Python transport interface consumed by driver protocol implementations;
- VISA resource communication;
- asynchronous or synchronous serial-port communication exposed through a synchronous RFDS interface;
- raw TCP socket communication;
- direct USB communication using control, bulk, or interrupt transfers;
- USB Test and Measurement Class communication when exposed through VISA;
- transport configuration schemas;
- resource enumeration and selection descriptors;
- open, close, read, write, transaction, flush, and optional clear operations;
- transport capability declaration;
- operation timing and bounded execution;
- safe retry rules;
- locking and transaction atomicity;
- reconnect behavior;
- trace hooks and protocol-boundary observation;
- deterministic simulator support;
- transport contract tests.

### 2.2 Out of scope

RFDS-004 does not define:

- the project-wide public Robot Framework keyword names;
- instrument-specific command syntax;
- SCPI command construction;
- Modbus, CAN, HTTP, REST, or vendor-protocol semantics;
- response parsing beyond transport framing;
- physical instrument behavior;
- measurement accuracy;
- calibration;
- bench topology;
- complete package release requirements;
- GUI connection controls;
- vendor driver installation procedures beyond the transport setup guide;
- operating-system device-driver implementation.

HTTP and REST may use the same architectural principles, but they require a separate protocol-aware HTTP transport specification unless a driver treats HTTP as a raw byte stream, which is not recommended.

---

## 3. Normative Terminology

- **shall / shall not** — mandatory requirement;
- **should / should not** — recommended requirement; deviations require documented justification;
- **may** — permitted implementation choice;
- **transport** — an object that exchanges bytes with one communication endpoint;
- **backend** — the implementation that adapts an external library or operating-system API to the RFDS transport interface;
- **protocol layer** — driver logic that creates device commands and parses device responses;
- **transaction** — one atomic outbound operation and its associated inbound response, when a response is expected;
- **endpoint** — a VISA resource, serial port, TCP host and port, or USB device/interface/endpoints;
- **session** — one successfully opened transport connection;
- **trace observer** — an approved component that records transport-boundary exchanges without changing them.

---

## 4. Design Principles

Every RFDS transport implementation shall follow these principles.

### 4.1 Byte-oriented canonical boundary

The canonical transport boundary shall exchange `bytes`.

Text encoding, text decoding, command terminators, response terminator stripping, SCPI formatting, and response interpretation shall be implemented above the core byte transport interface.

A backend shall not silently:

- change character encoding;
- add a terminator not declared by configuration or the caller;
- strip response bytes;
- normalize whitespace;
- change letter case;
- translate line endings;
- parse protocol content.

### 4.2 Protocol and transport separation

Device protocol code shall not directly import or call:

- `pyvisa`;
- `serial` or `pyserial`;
- `socket`;
- `usb`, `pyusb`, or native USB APIs;
- backend-specific resource or session objects.

All device communication shall pass through the RFDS transport interface or an approved capability extension.

### 4.3 Deterministic configuration

A transport shall use an explicit, validated configuration. Connection behavior shall not depend on hidden global state, implicit environment discovery, or uncontrolled backend defaults.

### 4.4 Bounded execution

No transport operation shall wait indefinitely. Open, read, write, transaction, flush, clear, and close operations shall have bounded behavior.

### 4.5 No unsafe implicit replay

The transport layer shall not automatically repeat a write or transaction after data may have reached the device unless the protocol layer explicitly marks the operation as safe to replay.

### 4.6 Observable protocol boundary

Every backend shall support an observation mechanism sufficient to prove the actual outbound and inbound bytes or structured USB operation used by RFDS-019 conformance testing.

### 4.7 Backend substitution

A driver protocol implementation shall be testable with a simulator or spy transport without changing its public Robot Framework API.

---

## 5. Required Architecture

Each driver shall separate communication into at least these logical components:

```text
Public Robot Framework library
├── Public keyword adapter
├── Driver state and safety layer
├── Device protocol implementation
├── Text/binary codec and framing
└── RFDS transport
    ├── Base interface
    ├── Configuration model
    ├── Error model
    ├── Trace observer interface
    └── Backend
        ├── VISA
        ├── Serial
        ├── TCP/IP
        ├── USB
        └── Simulator/spy
```

A driver may combine files when the implementation is small, but the responsibilities shall remain separable and testable.

The protocol layer shall own:

- command construction;
- protocol-level sequence and state;
- response grammar and parsing;
- device error queries;
- protocol-specific checksum or payload validation;
- command idempotency classification;
- device-specific recovery;
- command-specific timing and stabilization delays.

The transport layer shall own:

- endpoint connection;
- byte transfer;
- low-level transport framing only when required by the backend;
- transport timeout enforcement;
- resource locking;
- transport-state transitions;
- transport errors;
- trace emission;
- low-level reconnect support when explicitly requested.

---

## 6. Mandatory Package Layout

Each RFDS driver that implements a transport shall provide equivalent files to:

```text
rf_<driver_name>/
├── src/
│   └── rf_<driver_name>/
│       ├── transport/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── config.py
│       │   ├── errors.py
│       │   ├── models.py
│       │   ├── codec.py
│       │   ├── tracing.py
│       │   └── backends/
│       │       ├── __init__.py
│       │       ├── visa.py
│       │       ├── serial.py
│       │       ├── tcp.py
│       │       ├── usb.py
│       │       └── simulator.py
│       └── protocol/
├── tests/
│   ├── unit/
│   │   └── transport/
│   ├── integration/
│   │   └── transport/
│   └── conformance/
├── examples/
│   └── connection/
├── guide/
│   └── transport_setup.md
├── history/
└── review/
```

A driver shall include only the backends it supports. Unsupported backend modules may be omitted; they shall not be present as non-functional placeholders.

A shared RFDS transport package may be used instead of duplicated driver-local code. When used, the driver shall pin or constrain a compatible transport-package version and record it in release evidence.

---

## 7. Transport State Model

### 7.1 Required states

The transport shall expose one of these states:

| State | Meaning |
|---|---|
| `CREATED` | Object exists and configuration is available, but no session has been opened |
| `OPENING` | Backend open is in progress |
| `OPEN` | Session is available for I/O |
| `FAULTED` | The session failed or its validity is unknown |
| `CLOSING` | Close is in progress |
| `CLOSED` | No backend session or owned resource remains |

### 7.2 Required transitions

```text
CREATED ──open──> OPENING ──success──> OPEN
    │                 │                  │
    │                 └──failure──> FAULTED
    │                                    │
    └──close────────────────────────> CLOSED

OPEN ──I/O failure or disconnect──> FAULTED
OPEN ──close──> CLOSING ──success──> CLOSED
FAULTED ──close──> CLOSING ──success──> CLOSED
CLOSED ──open──> OPENING
```

### 7.3 State behavior

- `open()` shall fail with a transport state error when called during `OPENING` or `CLOSING`.
- `open()` called while already `OPEN` shall not create a second session. It may return the existing session descriptor only when the requested normalized configuration is identical; otherwise it shall fail.
- `close()` shall be idempotent when called in `CREATED` or `CLOSED`.
- I/O operations shall fail before transmission when the transport is not `OPEN`.
- A disconnect, backend session invalidation, or I/O failure that makes session validity uncertain shall place the transport in `FAULTED`.
- `FAULTED` shall not be treated as connected merely because a backend handle still exists.
- Reopening from `FAULTED` shall first release the failed session and its locks.

### 7.4 Health semantics

`is_open` shall report session state only. It shall not transmit a device command.

A device identity query, ping, status query, or other communication check belongs to the protocol layer.

---

## 8. Canonical Transport Interface

The following interface is normative in behavior. Exact Python names may vary only when mapped unambiguously in the architecture documentation.

```python
from typing import Protocol

class Transport(Protocol):
    @property
    def state(self) -> "TransportState": ...

    @property
    def descriptor(self) -> "TransportDescriptor": ...

    @property
    def capabilities(self) -> "TransportCapabilities": ...

    def open(self) -> "TransportDescriptor": ...

    def close(self) -> None: ...

    def write(
        self,
        data: bytes,
        *,
        timeout_s: float | None = None,
        operation_id: str | None = None,
    ) -> "WriteResult": ...

    def read(
        self,
        request: "ReadRequest",
        *,
        timeout_s: float | None = None,
        operation_id: str | None = None,
    ) -> bytes: ...

    def transact(
        self,
        outbound: bytes,
        response: "ReadRequest",
        *,
        timeout_s: float | None = None,
        replay_policy: "ReplayPolicy" = ReplayPolicy.NEVER,
        operation_id: str | None = None,
    ) -> bytes: ...

    def flush(self, direction: "FlushDirection") -> None: ...
```

### 8.1 Mandatory operations

Every transport backend shall implement:

- `open`;
- `close`;
- `write`;
- `read`;
- `transact`;
- `flush` or an explicit unsupported-capability result when the underlying transport cannot flush safely;
- state, descriptor, and capabilities inspection;
- context-manager cleanup or an equivalent deterministic cleanup mechanism.

### 8.2 Transaction atomicity

`transact()` shall hold the transport transaction lock from the first outbound byte through completion or failure of the corresponding read.

No other write, read, or transaction may interleave within that interval.

`transact()` shall not be implemented as an unlocked public call to `write()` followed by `read()`.

### 8.3 Return types

- `write()` shall return a structured result containing at least the number of bytes accepted for transmission and operation duration.
- `read()` and `transact()` shall return raw `bytes`.
- `close()` and successful `flush()` shall return `None`.
- Backend-native objects shall not be returned through the canonical interface.

### 8.4 Operation identifiers

Each operation should accept an optional operation identifier supplied by the protocol layer. The identifier shall be included in trace records and error evidence.

---

## 9. Required Data Models

### 9.1 Transport descriptor

The descriptor shall contain at least:

- transport kind;
- normalized endpoint identity;
- backend name;
- backend version when available;
- session identifier generated by the RFDS transport;
- open timestamp;
- stable device identity fields available without a protocol query;
- redacted display name safe for logs.

### 9.2 Transport capabilities

Capabilities shall be explicit rather than inferred from backend type.

Required capability fields include:

- can read;
- can write;
- supports transactions;
- supports binary transfers;
- supports resource discovery;
- supports input flush;
- supports output flush;
- supports device clear;
- supports exclusive locking;
- supports transport tracing;
- supports reconnect;
- supports serial control lines;
- supports USB control transfers;
- supports USB bulk transfers;
- supports USB interrupt transfers.

### 9.3 Write result

A write result shall contain at least:

- requested byte count;
- accepted or transmitted byte count as reported by the backend;
- duration;
- whether the backend reported complete transfer;
- operation identifier;
- session identifier.

A short write shall fail unless the backend can continue deterministically and complete the remaining bytes within the same operation.

### 9.4 Read request

A read request shall use one explicit mode:

| Mode | Required behavior |
|---|---|
| `UNTIL_TERMINATOR` | Read through the configured terminator, subject to size and timeout limits |
| `EXACT_LENGTH` | Read exactly the declared number of bytes |
| `UP_TO_LENGTH` | Read no more than the declared maximum and return according to backend completion rules |
| `AVAILABLE` | Read currently available bytes without waiting beyond the bounded availability timeout |
| `BACKEND_DEFINED_MESSAGE` | Use only when the backend has a documented message-boundary mechanism, such as VISA end indication |

A request shall define, as applicable:

- mode;
- exact or maximum length;
- terminator;
- include or exclude terminator in returned bytes;
- maximum response size;
- empty-response policy;
- first-byte timeout;
- inter-byte timeout;
- total timeout.

Unbounded read size is prohibited.

---

## 10. Text Codec and Terminator Rules

### 10.1 Codec separation

A text codec shall be a separate protocol-layer component or transport-adjacent utility. The byte transport shall remain usable without it.

A text codec shall declare:

- character encoding;
- encoding error policy;
- outbound terminator;
- inbound terminator;
- whether an existing outbound terminator is preserved or rejected;
- whether the inbound terminator is returned or removed;
- maximum encoded command size;
- maximum decoded response size.

### 10.2 Defaults

A driver may use ASCII as its documented default for ASCII instrument protocols. The encoding shall still be explicit in configuration or driver constants.

Decoding errors shall use strict handling by default. Replacement-character decoding is prohibited for protocol responses unless the protocol explicitly permits corrupted or non-text bytes.

### 10.3 Terminator behavior

- A terminator shall not be appended twice.
- Empty terminators shall be represented explicitly as `b""` or `None` according to the implementation model.
- `None` shall mean no transport terminator behavior.
- A zero-length response shall not be confused with a terminator-only response.
- Inbound terminator stripping shall remove only the exact declared final terminator.
- Generic `.strip()` or `.rstrip()` shall not be used on raw protocol data.

### 10.4 Binary data

Binary operations shall bypass text encoding and decoding.

The transport shall not:

- strip zero bytes;
- reinterpret byte order;
- convert binary payloads to text;
- apply line-ending conversion;
- treat an embedded terminator byte as an end marker when exact-length mode is selected.

---

## 11. Common Transport Configuration

Every transport configuration shall define or inherit these common fields:

```yaml
transport:
  type: visa | serial | tcp | usb | simulator
  endpoint: "backend-specific endpoint"
  open_timeout_s: 5.0
  read_timeout_s: 5.0
  write_timeout_s: 5.0
  transaction_timeout_s: 10.0
  close_timeout_s: 2.0
  lock_timeout_s: 5.0
  max_write_bytes: 1048576
  max_read_bytes: 1048576
  exclusive: true
  encoding: ascii
  write_terminator: "\\n"
  read_terminator: "\\n"
  trace:
    enabled: false
    payload_mode: metadata
    redact_patterns: []
```

### 11.1 Validation

Configuration shall be validated before backend open begins.

Validation shall reject:

- unknown mandatory fields;
- unsupported transport types;
- negative or zero timeouts where zero does not have an explicitly documented meaning;
- response limits smaller than required protocol framing;
- invalid endpoint syntax;
- incompatible flow-control options;
- ambiguous USB selectors;
- invalid endpoint numbers or transfer types;
- mutually exclusive configuration values;
- unsupported capabilities requested as mandatory.

### 11.2 Immutability

The normalized connection configuration shall be immutable while a session is open.

A change that affects endpoint, timing, framing, encoding, flow control, USB interface ownership, or resource locking shall require close and reopen.

Per-operation timeout overrides and read requests are permitted and do not mutate the session configuration.

### 11.3 Secrets

Credentials, tokens, private keys, and other secrets shall not be embedded in a plain endpoint string when a structured secret mechanism is available.

Secrets shall not appear in:

- exception messages;
- trace payload previews;
- Robot Framework logs;
- generated evidence;
- README examples;
- AI contracts.

---

## 12. Timeout Requirements

### 12.1 Timeout categories

The transport shall distinguish:

- open timeout;
- resource-lock timeout;
- first-byte read timeout;
- inter-byte timeout where supported;
- total read timeout;
- write timeout;
- total transaction timeout;
- close timeout.

### 12.2 Monotonic timing

Elapsed time and timeout enforcement shall use a monotonic clock.

Wall-clock timestamps may be included in evidence, but shall not be used to determine operation timeout.

### 12.3 Timeout precedence

For each operation:

1. a valid per-operation override shall take precedence;
2. otherwise the normalized transport configuration shall apply;
3. backend infinite-timeout defaults shall never apply silently.

### 12.4 Transaction timeout

The total transaction timeout shall bound:

- lock acquisition;
- write;
- any declared query delay;
- read;
- transport-level cleanup triggered by the failed transaction.

A backend shall not restart the complete timeout for every internal read chunk unless the read request explicitly defines an inter-byte timeout in addition to a total timeout.

### 12.5 Timeout result

A timeout shall raise a typed transport timeout error containing:

- timed-out phase;
- configured timeout;
- elapsed duration;
- bytes written;
- bytes read;
- whether outbound transmission may have occurred;
- whether the operation is safe to retry;
- transport state after the timeout.

---

## 13. Cancellation and Robot Framework Stop Behavior

Transport operations shall be implemented so that Robot Framework execution can regain control after the configured timeout.

A backend shall not rely on an uninterruptible blocking call without an external bound.

When the underlying API cannot cancel an in-progress operation directly, the implementation shall use one of:

- native per-call timeout;
- a bounded worker with deterministic teardown;
- session close from a controlled cancellation path;
- an approved backend-specific abort operation.

Cancellation or forced close shall not leave a lock permanently held.

The transport shall document whether cancellation invalidates the current session. When validity is uncertain, state shall become `FAULTED`.

---

## 14. Retry and Replay Policy

### 14.1 Default policy

The default replay policy for all write and transaction operations shall be `NEVER`.

### 14.2 Permitted automatic retries

An automatic retry may occur only when one of these is proven:

- no outbound byte was transmitted;
- connection establishment failed before a session was created;
- the protocol layer explicitly marked the operation as idempotent and safe to replay;
- a read-only transaction is documented as replay-safe;
- a backend-internal partial operation can be completed without repeating already accepted data.

### 14.3 Prohibited automatic retries

The transport shall not automatically replay after an uncertain write for operations that may:

- enable an output;
- change voltage, current, load, temperature, relay, or motion state;
- trigger acquisition;
- clear data;
- save configuration;
- reset, reboot, calibrate, erase, or update firmware;
- perform any non-idempotent device action.

### 14.4 Retry evidence

Every retry shall emit trace evidence containing:

- attempt number;
- reason;
- bytes known to have been transmitted;
- replay policy;
- delay before retry;
- final outcome.

---

## 15. Thread Safety and Concurrency

### 15.1 Session serialization

A transport session shall permit only one active I/O operation or transaction unless the backend and protocol explicitly support multiplexing.

Instrument transports shall be serialized by default.

### 15.2 Lock scope

- `write()` shall hold the session lock for the complete write.
- `read()` shall hold the session lock for the complete read.
- `transact()` shall hold the same lock across write and read.
- `close()` shall coordinate with active operations and shall not free the backend session while another thread is using it.
- trace callbacks shall not be allowed to re-enter the same transport operation.

### 15.3 Multiple transport objects

Creating two transport objects for the same exclusive endpoint shall fail or be prevented by a documented resource-lock mechanism.

A backend-only in-process mutex is insufficient when multiple processes may access the same physical resource. The implementation shall use backend or operating-system locking where available and document limitations where it is not available.

### 15.4 Async backends

An asynchronous backend may be used internally, but it shall expose the required synchronous behavior to the RFDS driver unless the project defines a separate asynchronous driver standard.

The backend shall not create unmanaged event loops or background threads that survive `close()`.

---

## 16. Resource Discovery and Selection

### 16.1 Discovery separation

Discovery shall be a separate operation from opening a transport.

Discovery shall not:

- connect to every discovered device unless explicitly requested;
- send protocol commands by default;
- select the first matching device silently;
- mutate driver connection state.

### 16.2 Resource descriptor

Discovery results shall use a common descriptor containing, as applicable:

- transport type;
- stable resource identifier;
- display name;
- VISA resource name;
- serial port name and hardware path;
- host and port;
- USB vendor ID and product ID;
- USB serial number;
- USB bus, port path, interface, and endpoints;
- manufacturer and product strings when safely available;
- permission or availability status;
- whether the resource is currently in use;
- discovery source.

### 16.3 Deterministic selection

When more than one resource matches, selection shall require a stable discriminator such as:

- exact VISA resource name;
- USB serial number;
- serial-port hardware identifier;
- configured IP address and port;
- approved alias mapped to one stable endpoint.

Selecting only by USB VID/PID is insufficient when more than one matching device is present.

### 16.4 Discovery errors

Permission-denied, unavailable-backend, malformed-descriptor, and transient enumeration failures shall remain distinguishable from an empty discovery result.

---

## 17. Transport Error Model

### 17.1 Required hierarchy

The transport shall expose a stable error hierarchy equivalent to:

```text
TransportError
├── TransportConfigurationError
├── TransportBackendUnavailableError
├── TransportDeviceNotFoundError
├── TransportPermissionError
├── TransportResourceBusyError
├── TransportStateError
├── TransportOpenError
├── TransportCloseError
├── TransportTimeoutError
│   ├── TransportOpenTimeoutError
│   ├── TransportReadTimeoutError
│   ├── TransportWriteTimeoutError
│   └── TransportTransactionTimeoutError
├── TransportDisconnectedError
├── TransportReadError
├── TransportWriteError
├── TransportShortTransferError
├── TransportFramingError
├── TransportCapabilityError
└── TransportInternalError
```

A backend may add more specific subclasses while preserving the stable RFDS category.

This `TransportError` hierarchy is internal to the transport boundary, not the public driver-facing hierarchy. At the protocol/driver boundary, transport failures shall be translated into the corresponding RFDS-007 `DriverError` categories (principally `DriverTransportError`, including `DriverTimeoutError` for the timeout subtree); RFDS-007 remains authoritative for how a translated failure is represented to callers and Robot Framework.

### 17.2 Error content

Every transport error shall provide machine-readable fields equivalent to:

- stable error code;
- human-readable message;
- transport kind;
- redacted endpoint;
- backend name;
- operation;
- operation identifier;
- session identifier when available;
- state before and after failure;
- timeout and elapsed duration when applicable;
- bytes written and read;
- retryable flag;
- replay-safe flag;
- backend-native error code when available;
- original exception type without exposing secrets.

### 17.3 Exception translation

Backend-native exceptions shall be translated at the backend boundary.

Protocol code and public Robot Framework keywords shall not need to catch backend-specific exception classes.

### 17.4 Protocol errors

A valid device response that reports a device or protocol error is not a transport error. It shall be handled by the device protocol error model.

Malformed transport framing, truncated transfer, missing terminator, or invalid transfer length may be transport errors when the transport contract defines that framing.

---

## 18. Trace and Observability Requirements

### 18.1 Required trace events

Every backend shall emit or make available equivalent events for:

- open requested;
- open succeeded or failed;
- lock acquired or failed;
- write started;
- write completed or failed;
- read started;
- read chunk received when chunk evidence is enabled;
- read completed or failed;
- transaction started and completed;
- flush or clear;
- retry;
- disconnect detected;
- close requested;
- close completed or failed;
- state transition.

### 18.2 Trace record fields

Each trace record shall contain at least:

- wall-clock timestamp;
- monotonic elapsed time or monotonic sequence context;
- sequence number;
- transaction identifier;
- operation identifier;
- session identifier;
- transport type;
- redacted endpoint;
- direction;
- event type;
- byte count;
- duration where applicable;
- result status;
- error code when applicable.

Payload evidence shall support one or more configured modes:

- none;
- metadata only;
- hash;
- bounded hexadecimal preview;
- bounded escaped-text preview;
- full payload for approved conformance environments.

### 18.3 Trace observer behavior

A trace observer shall not:

- modify outbound or inbound bytes;
- introduce unbounded blocking;
- raise an exception that changes the primary I/O result;
- expose secrets;
- reorder trace records.

Trace observer failures shall be reported separately. They shall not silently remove required conformance evidence.

### 18.4 RFDS-019 integration

The observation point shall be close enough to the physical or simulated device boundary to prove:

- what bytes, VISA operation, serial frame, TCP payload, or USB transfer the driver attempted;
- what response was returned to the protocol layer;
- which public keyword and protocol vector produced the exchange.

Internal protocol-method mocking alone is insufficient for transport conformance.

---

## 19. VISA Backend Requirements

### 19.1 Scope

The VISA backend shall support VISA resources appropriate to the driver, including one or more of:

- USBTMC;
- GPIB;
- TCPIP INSTR;
- TCPIP SOCKET;
- ASRL;
- PXI or VXI when required by a device-specific driver.

A driver shall declare which resource families are supported and tested.

### 19.2 Configuration

The VISA configuration shall include, as applicable:

- exact VISA resource name;
- VISA implementation or backend selection policy;
- access mode;
- open timeout;
- operation timeout;
- read termination;
- write termination;
- chunk size;
- query delay;
- send-end behavior;
- suppress-end behavior;
- interface-specific attributes explicitly required by the driver.

The driver shall not rely on whichever VISA implementation happens to be selected by the local environment unless that policy is documented and tested.

### 19.3 Raw operations

The RFDS VISA adapter should use raw byte operations where available so that the canonical transport behavior remains byte exact.

When backend text operations are used, their encoding and termination behavior shall be proven equivalent to the RFDS codec configuration.

### 19.4 VISA clear and status operations

VISA clear, trigger, status-byte read, event handling, or interface-specific control shall be exposed only through declared capability extensions.

Opening a resource shall not automatically issue device clear, reset, remote mode, or identity commands unless a device-specific requirement explicitly mandates it.

### 19.5 VISA errors

VISA status codes shall be translated to the RFDS error hierarchy while preserving the native code in machine-readable evidence.

A VISA timeout shall not be reported as an empty valid response.

### 19.6 VISA locking

Exclusive or shared VISA locking shall be explicit. When exclusive mode is requested and the backend cannot guarantee it, open shall fail or the limitation shall be approved and documented.

---

## 20. Serial Backend Requirements

### 20.1 Configuration

The serial configuration shall define:

- exact port or stable hardware path;
- baud rate;
- data bits;
- parity;
- stop bits;
- read timeout;
- write timeout;
- inter-byte timeout where required;
- XON/XOFF;
- RTS/CTS;
- DSR/DTR flow control;
- initial DTR state;
- initial RTS state;
- exclusive-open behavior where supported;
- input and output buffer reset policy;
- break condition policy;
- read and write terminators when used by the protocol codec.

### 20.2 Control-line safety

The initial DTR and RTS states shall be explicit because opening a serial port may change hardware outputs or reset connected equipment.

A serial backend shall not toggle DTR, RTS, break, or other control lines implicitly beyond unavoidable operating-system behavior. Any unavoidable behavior shall be documented in the guide and driver limitations.

### 20.3 Buffer handling

The backend shall not flush serial input automatically on every write or transaction.

Input or output flush shall occur only when:

- explicitly requested;
- required by a documented recovery sequence;
- performed during open according to an explicit configuration policy.

Discarded bytes shall be traceable in diagnostic mode.

### 20.4 Partial reads

Serial reads shall correctly handle fragmented arrival. Completion shall be determined by the explicit read mode, not by one low-level read call returning fewer bytes than requested.

### 20.5 Framing and checksums

Protocol-level frames, addresses, length fields, and checksums belong to the protocol layer unless the serial backend is specifically defined as a framed-serial backend. Such a backend shall be a separate declared transport type or capability, not hidden behavior in the generic serial adapter.

### 20.6 Hot unplug

A serial device removal or invalid file handle shall raise a disconnected error and place the session in `FAULTED`.

---

## 21. TCP/IP Backend Requirements

### 21.1 Scope

The generic TCP/IP backend defined here is a raw TCP client transport.

It shall not implement HTTP, REST, WebSocket, or application-protocol semantics.

### 21.2 Configuration

The TCP configuration shall define:

- host name or IP address;
- port;
- address-family policy;
- connect timeout;
- DNS resolution timeout or bounded resolution policy;
- read timeout;
- write timeout;
- TCP keepalive enabled or disabled;
- keepalive parameters where supported;
- `TCP_NODELAY` policy;
- local bind address when required;
- receive and send buffer settings only when explicitly needed;
- TLS enabled or disabled;
- TLS server name and verification policy when TLS is enabled.

### 21.3 DNS and multiple addresses

When a host name resolves to multiple addresses, connection attempts shall follow a documented bounded strategy. Failure evidence shall identify attempted addresses without exposing secrets.

### 21.4 Stream semantics

TCP is a byte stream. The backend shall not assume that:

- one `send` equals one device message;
- one `recv` equals one complete response;
- one response arrives in one packet;
- packet boundaries are protocol boundaries.

The explicit read request shall determine completion.

### 21.5 Connection closure

A zero-length socket receive shall be treated as peer closure, not as a valid empty protocol response.

Broken pipe, reset, aborted connection, and unreachable network errors shall map to stable RFDS categories.

### 21.6 Keepalive and health

TCP keepalive may help detect stale connections, but shall not be represented as proof that the instrument protocol is responsive.

### 21.7 TLS

When TLS is used:

- certificate verification shall be enabled by default;
- disabling verification shall require explicit configuration and a documented risk;
- private key and credential data shall be redacted;
- TLS handshake timeout shall be included in open timeout behavior.

### 21.8 Reconnect

Automatic reconnect shall not replay an uncertain command or transaction. Reconnect may restore a session only; the protocol layer shall decide whether and how to repeat a device operation.

---

## 22. Direct USB Backend Requirements

### 22.1 Scope

The direct USB backend applies when a driver communicates using USB control, bulk, or interrupt transfers without VISA.

USBTMC devices accessed through VISA shall use the VISA backend unless a documented reason requires direct USB access.

### 22.2 Device selection

USB configuration shall support stable selection using:

- vendor ID;
- product ID;
- device serial number;
- bus and physical port path when serial number is unavailable;
- configuration number;
- interface number;
- alternate setting;
- endpoint addresses;
- expected transfer types.

When more than one device matches and no stable discriminator is provided, open shall fail with an ambiguity error.

### 22.3 Interface ownership

The configuration shall declare:

- whether a kernel driver may be detached;
- whether the USB interface shall be claimed exclusively;
- whether the kernel driver shall be reattached during close;
- expected device configuration;
- cleanup behavior after failed open.

A backend shall not detach an operating-system driver from an unrelated interface.

### 22.4 Transfer operations

Direct USB capability extensions may provide:

- control transfer;
- bulk write;
- bulk read;
- interrupt write;
- interrupt read.

Each transfer shall declare:

- direction;
- endpoint or control request fields;
- timeout;
- requested length;
- maximum response length;
- short-packet policy;
- zero-length-packet policy when relevant.

### 22.5 Control transfer evidence

A control-transfer trace shall record, subject to redaction:

- request type;
- request;
- value;
- index;
- requested length;
- actual length;
- direction;
- payload or payload evidence.

### 22.6 Short transfers

A short USB transfer shall be handled according to the declared transfer semantics. It shall not be silently accepted when an exact-length response is required.

### 22.7 USB reset

USB device reset shall not occur automatically during normal open, timeout recovery, or close. It requires an explicit capability and device-specific safety decision.

### 22.8 Hot unplug and re-enumeration

Hot unplug shall place the session in `FAULTED`.

Re-enumeration may change bus address. Reconnect shall use the configured stable selector rather than a stale temporary address.

---

## 23. Simulator and Spy Transport

### 23.1 Purpose

A simulator or spy transport shall enable deterministic verification of protocol serialization, response parsing, timeout handling, malformed data, disconnects, and recovery.

### 23.2 Boundary equivalence

The simulator shall operate at the same transport interface used by the physical backend. Driver protocol code shall not require a special test-only call path.

### 23.3 Scripted vectors

A simulator should support scripted vectors defining:

- expected outbound bytes or structured USB call;
- outbound comparison mode;
- response bytes;
- response delay;
- chunked response schedule;
- timeout behavior;
- disconnect point;
- partial-write behavior;
- malformed or truncated response;
- injected backend error;
- expected retry policy;
- required cleanup.

### 23.4 Strict behavior

Unexpected writes, missing expected writes, extra reads, incorrect operation order, and unconsumed scripted vectors shall fail the test.

A permissive simulator that returns success for unknown commands shall not be used as the only conformance oracle.

### 23.5 Spy behavior

A spy transport shall delegate to a real transport while recording exact operations. It shall preserve ordering, timing semantics, bytes, exceptions, and return values.

---

## 24. Capability Extensions

Backend-specific functions shall use explicit capability interfaces rather than unchecked backend downcasts.

Examples include:

```text
VisaControlCapability
- device_clear()
- read_status_byte()
- trigger()

SerialLineCapability
- set_dtr(state)
- set_rts(state)
- get_cts()
- get_dsr()
- send_break(duration)

UsbControlCapability
- control_transfer(...)

UsbBulkCapability
- bulk_write(...)
- bulk_read(...)
```

A protocol implementation shall verify capability availability before use and shall raise a stable transport capability error when unavailable.

Public Robot Framework keyword behavior shall not change silently merely because a different backend lacks an extension.

---

## 25. Open, Close, and Recovery Rules

### 25.1 Open sequence

A backend open shall perform only the minimum transport operations required to create a usable session:

1. validate normalized configuration;
2. acquire resource lock when required;
3. create backend session;
4. configure transport attributes;
5. claim required USB or operating-system resources;
6. verify that the session can perform transport I/O without sending an instrument protocol command;
7. publish descriptor and capabilities;
8. enter `OPEN`.

Identity queries, device resets, output changes, remote-mode commands, and protocol handshakes belong to driver setup unless specifically required to establish the transport itself.

### 25.2 Failed open cleanup

A failed open shall release:

- partial backend sessions;
- resource locks;
- claimed USB interfaces;
- detached kernel-driver state where safe;
- worker threads or event loops;
- temporary files or proxies.

The resulting state shall be `FAULTED` or `CLOSED` according to whether cleanup completed successfully. The implementation shall document the rule.

### 25.3 Close sequence

Close shall:

- stop accepting new operations;
- wait for, cancel, or bound active operations;
- release backend session resources;
- release locks and claimed interfaces;
- stop transport-owned workers;
- emit final trace events;
- enter `CLOSED`.

Close shall not send instrument-specific shutdown or output-disable commands. Those belong to the driver teardown and safety layer.

### 25.4 Recovery

Transport recovery may include:

- input flush;
- output flush when safe;
- closing a failed session;
- reopening the same normalized endpoint;
- reapplying transport attributes;
- reclaiming a USB interface.

Transport recovery shall not include hidden device reset, command replay, output changes, or protocol-state reconstruction.

The protocol layer shall verify communication after transport recovery using a known-good protocol operation.

---

## 26. Logging, Diagnostics, and Metrics

The transport shall expose diagnostics sufficient for troubleshooting without exposing backend objects.

Recommended session metrics include:

- open count;
- close count;
- bytes written;
- bytes read;
- write count;
- read count;
- transaction count;
- timeout count;
- disconnect count;
- retry count;
- last successful I/O time;
- last error code;
- maximum observed operation duration;
- current state;
- current session identifier.

Metrics shall not be used as protocol truth. For example, bytes written does not prove that a device executed a command.

Payload logging shall be disabled or bounded in normal production operation and enabled explicitly for conformance or troubleshooting.

---

## 27. Configuration Examples

### 27.1 VISA

```yaml
transport:
  type: visa
  resource_name: "USB0::0x2A8D::0x0101::MY12345678::INSTR"
  backend: system
  access_mode: exclusive
  open_timeout_s: 5.0
  read_timeout_s: 5.0
  write_timeout_s: 5.0
  transaction_timeout_s: 10.0
  read_terminator: "\\n"
  write_terminator: "\\n"
  encoding: ascii
  chunk_size: 20480
  query_delay_s: 0.0
```

### 27.2 Serial

```yaml
transport:
  type: serial
  port: "COM4"
  baudrate: 38400
  bytesize: 8
  parity: none
  stopbits: 1
  xonxoff: false
  rtscts: false
  dsrdtr: false
  initial_dtr: false
  initial_rts: false
  exclusive: true
  open_timeout_s: 3.0
  read_timeout_s: 2.0
  write_timeout_s: 2.0
  inter_byte_timeout_s: 0.2
  read_terminator: null
  write_terminator: null
```

### 27.3 Raw TCP/IP

```yaml
transport:
  type: tcp
  host: "192.168.0.55"
  port: 5025
  address_family: any
  open_timeout_s: 3.0
  read_timeout_s: 3.0
  write_timeout_s: 3.0
  transaction_timeout_s: 6.0
  keepalive: true
  tcp_nodelay: true
  tls:
    enabled: false
  read_terminator: "\\n"
  write_terminator: "\\n"
  encoding: ascii
```

### 27.4 Direct USB bulk transport

```yaml
transport:
  type: usb
  vendor_id: 0x1234
  product_id: 0x5678
  serial_number: "SN000123"
  configuration: 1
  interface: 0
  alternate_setting: 0
  detach_kernel_driver: false
  claim_exclusive: true
  endpoints:
    out: 0x01
    in: 0x81
  open_timeout_s: 5.0
  read_timeout_s: 2.0
  write_timeout_s: 2.0
  max_read_bytes: 65536
```

### 27.5 Simulator

```yaml
transport:
  type: simulator
  vector_file: "tests/conformance/data/protocol_vectors.yaml"
  strict_order: true
  fail_on_unconsumed_vectors: true
  default_timeout_s: 1.0
  trace:
    enabled: true
    payload_mode: full
```

---

## 28. Robot Framework Integration

### 28.1 Internal status

The transport interface is an internal driver contract. It shall not automatically expose all transport methods as public Robot Framework keywords.

Public connection keywords shall delegate to the driver lifecycle layer, which then opens or closes the configured transport.

### 28.2 Robot-compatible results

When transport information is intentionally returned through a public diagnostic keyword, values shall be converted to Robot Framework-compatible scalar, list, or dictionary types.

Backend objects, exception instances, sockets, serial handles, VISA resources, USB device objects, locks, and byte iterators shall not be returned to Robot Framework.

Raw binary responses may be returned only when the public API explicitly documents bytes behavior and the AI driver contract declares the return type.

### 28.3 Error reporting

Transport errors propagated to Robot Framework shall preserve:

- stable error category;
- concise operator-readable message;
- actionable endpoint and configuration context after redaction;
- retryability and session-state information where relevant.

A public keyword shall not expose an uncontrolled backend stack trace as its only diagnostic.

---

## 29. Integration with RFDS-017 AI Driver Contract

Each RFDS-017 AI driver contract shall declare, as applicable:

- supported transport types;
- default and alternative connection profiles;
- required endpoint fields;
- exclusive-resource requirements;
- timeout behavior;
- reconnect policy;
- safe and unsafe retry behavior;
- transport errors visible to public keywords;
- setup and teardown requirements;
- operator actions and permissions;
- stable resource-selection rules;
- protocol trace availability;
- transport limitations.

Each device-facing capability shall identify its transport or connection precondition and any command-specific timeout override.

The AI contract shall not expose secrets.

---

## 30. Integration with RFDS-018 AI Test Bench Contract

The RFDS-018 test-bench contract shall identify shared transport resources, including:

- VISA resources;
- USB devices and interfaces;
- serial ports;
- network addresses and ports;
- exclusive locks;
- USB hubs or network adapters that affect availability;
- operator connection steps;
- fixture-owned interfaces;
- resource conflicts;
- permitted simulator profiles.

The bench contract shall use stable resource identifiers where possible and shall not assume that operating-system enumeration order is fixed.

---

## 31. Integration with RFDS-019 Protocol Conformance

RFDS-004 shall provide the transport evidence required by RFDS-019.

For each device-facing public keyword, the conformance environment shall be able to associate:

- public Robot Framework keyword;
- canonical driver method;
- protocol vector;
- transport session;
- outbound transfer;
- inbound transfer when applicable;
- timeout or transport error;
- recovery operation;
- subsequent known-good call.

A backend passes transport observation only when the recorded operation proves the serialized exchange at the device boundary or an approved equivalent boundary.

---

## 32. Security and Safety Requirements

### 32.1 Least surprise

Opening a transport shall not change instrument output, trigger a measurement, reset a device, erase data, or start firmware update.

### 32.2 Unsafe retries

Writes with uncertain completion shall be treated as potentially executed. They shall not be replayed automatically unless explicitly classified as safe.

### 32.3 Resource ownership

The backend shall release serial ports, VISA sessions, sockets, USB interfaces, and process locks during normal close and failed initialization.

### 32.4 Network security

For network transports:

- TLS verification shall be enabled when TLS is used;
- credentials shall be protected and redacted;
- untrusted hostnames, redirected endpoints, or dynamically supplied ports shall be validated by the driver application where applicable;
- listening server sockets shall not be created by a client transport unless explicitly required.

### 32.5 USB safety

Kernel-driver detachment, configuration changes, interface claiming, and USB reset shall be limited to the exact selected device and interface.

### 32.6 Diagnostic payloads

Protocol traces may contain serial numbers, configuration values, or proprietary command data. Full payload traces shall be stored only in approved evidence locations.

---

## 33. Performance and Resource Requirements

- A driver shall not open and close the transport for every normal command.
- A transport shall avoid unbounded receive buffers.
- Trace buffering shall be bounded or streamed.
- Background workers shall be stopped during close.
- A transport shall not busy-wait while awaiting data.
- Query delay shall be explicit and shall not replace correct timeout handling.
- Chunk size shall be configurable only where it materially affects the backend.
- Large binary transfers shall avoid unnecessary repeated copies when practical.
- Performance optimization shall not weaken transaction locking, evidence, timeout enforcement, or error classification.

Device-specific performance targets belong to the implementation task or performance specification.

---

## 34. Mandatory Tests

Each implemented backend shall provide automated tests for the following categories.

### 34.1 Configuration tests

- valid configuration accepted;
- unknown or invalid fields rejected;
- ambiguous USB selection rejected;
- incompatible serial flow-control settings rejected;
- invalid timeout and size limits rejected;
- immutable open-session configuration enforced;
- secret redaction verified.

### 34.2 State tests

- initial state;
- successful open;
- failed open cleanup;
- duplicate open behavior;
- idempotent close;
- I/O before open rejected;
- I/O after close rejected;
- I/O failure enters `FAULTED` where required;
- reopen after fault;
- close during active operation remains bounded.

### 34.3 Transfer tests

- exact outbound bytes;
- complete write;
- short write;
- exact-length read;
- terminator read;
- fragmented response;
- empty response;
- response at maximum size;
- response over maximum size;
- binary payload containing zero and terminator bytes;
- partial response timeout;
- peer disconnect;
- flush behavior;
- transaction lock atomicity.

### 34.4 Timeout tests

- open timeout;
- lock timeout;
- write timeout;
- first-byte timeout;
- inter-byte timeout;
- total read timeout;
- transaction timeout;
- close timeout;
- no infinite backend defaults.

### 34.5 Retry tests

- no replay by default;
- retry allowed before any bytes sent;
- unsafe uncertain write not replayed;
- explicitly replay-safe query retried according to policy;
- retry evidence generated;
- maximum attempt count enforced.

### 34.6 Trace tests

- required events emitted;
- order preserved;
- payload exact in full-evidence mode;
- redaction applied;
- observer failure isolated;
- keyword, vector, operation, and session correlation present.

### 34.7 Backend-specific tests

VISA tests shall include:

- resource open and close;
- timeout mapping;
- exact raw write and read;
- VISA lock behavior;
- backend status-code preservation.

Serial tests shall include:

- port configuration;
- DTR and RTS initial state;
- fragmented input;
- buffer flush behavior;
- hot unplug or simulated disconnect;
- exclusive-open behavior where supported.

TCP tests shall include:

- fragmented packets;
- partial sends;
- peer graceful close;
- reset connection;
- DNS or multi-address failure strategy;
- keepalive configuration;
- TLS verification when supported.

USB tests shall include:

- deterministic device selection;
- interface claim and release;
- endpoint validation;
- control-transfer field capture;
- bulk short packet;
- timeout;
- hot unplug;
- failed-open cleanup;
- kernel-driver detach and reattach policy where enabled.

---

## 35. Transport Contract Test Suite

Each transport backend shall pass a shared contract suite using the same behavioral test cases.

The suite shall verify at least:

| Contract area | Required result |
|---|---|
| Interface implementation | All mandatory operations implemented |
| State model | All mandatory transitions conform |
| Byte preservation | Exact bytes preserved |
| Bounded execution | No operation exceeds its allowed timeout beyond documented scheduling tolerance |
| Transaction atomicity | No interleaving between write and associated read |
| Error translation | Backend errors map to stable RFDS categories |
| Resource cleanup | Handles, locks, interfaces, and workers released |
| Traceability | Required events and correlation fields present |
| Retry safety | No unsafe implicit replay |
| Backend substitution | Same protocol test passes with simulator and selected physical backend |

The contract suite should be reusable across driver packages or supplied by a shared RFDS transport package.

---

## 36. Test Profiles

The transport tests shall support these profiles where applicable:

- **unit** — no physical backend dependency;
- **simulator** — deterministic protocol and transport fault injection;
- **loopback** — serial loopback, TCP loopback server, or approved USB test endpoint;
- **real-device read-only** — safe identity and read operations;
- **real-device controlled** — approved commands with cleanup;
- **conformance trace** — full RFDS-019 evidence generation.

A test requiring unavailable hardware may be skipped only with a documented prerequisite. Simulator coverage remains mandatory for transport fault paths that are impractical to reproduce safely on hardware.

---

## 37. Documentation Requirements

Each supported backend shall document:

- required Python package or system backend;
- supported operating systems;
- driver installation prerequisites;
- permission setup;
- resource discovery procedure;
- stable endpoint selection;
- configuration fields and defaults;
- timeout behavior;
- line termination and encoding;
- exclusive-access behavior;
- hotplug and reconnect limitations;
- trace enablement;
- common error messages;
- safe troubleshooting procedure;
- cleanup and shutdown behavior.

The PyCharm and Robot Framework guide shall include at least one connection example for every supported transport type.

README, GitHub Pages, examples, AI contract, history, and review documents shall be updated in the same driver revision whenever transport behavior changes.

---

## 38. Lifecycle and Change Control

Transport implementation shall follow the RFDS driver implementation lifecycle.

### Gate 1 — Architecture and skeleton

- transport interface;
- state model;
- configuration models;
- errors;
- backend skeleton;
- simulator skeleton;
- architecture documentation.

### Gate 2 — Core implementation

- open and close;
- byte write and read;
- transaction locking;
- timeout enforcement;
- initial tests;
- first supported backend.

### Gate 3 — Extended features

- remaining backends;
- discovery;
- capability extensions;
- tracing;
- retry policy;
- recovery;
- fault injection.

### Gate 4 — Tests and documentation

- shared transport contract suite;
- backend integration tests;
- Robot Framework examples;
- setup guide;
- conformance profile;
- AI metadata update.

### Gate 5 — Review and release

- architecture review;
- transport safety review;
- code review;
- conformance evidence;
- issue correction;
- history and review update;
- release package.

Any change to endpoint syntax, default timeout, terminator behavior, retry policy, resource locking, error category, trace format, or backend capability shall update tests and documentation in the same revision.

---

## 39. Acceptance Criteria

An RFDS transport implementation passes RFDS-004 only when:

1. device protocol code depends only on the RFDS transport interface and declared capability extensions;
2. canonical I/O is byte oriented;
3. all supported backends implement the mandatory lifecycle and I/O contract;
4. configuration is validated before open;
5. no operation uses an uncontrolled infinite timeout;
6. read size is bounded;
7. transactions are atomic and cannot interleave;
8. backend exceptions are translated to stable RFDS errors;
9. transport state remains accurate after open, close, timeout, disconnect, and failed recovery;
10. no uncertain write is replayed automatically without explicit replay approval;
11. resource discovery does not silently select among ambiguous devices;
12. serial DTR and RTS behavior is explicit;
13. TCP stream fragmentation is handled correctly;
14. USB device and interface ownership is deterministic and safely released;
15. traces can prove outbound and inbound transport operations for RFDS-019;
16. simulator fault injection covers timeout, malformed transfer, partial transfer, and disconnect behavior;
17. all mandatory shared transport contract tests pass;
18. supported real backends pass their applicable integration profile;
19. transport resources, locks, workers, and claimed interfaces are released after close and failed open;
20. documentation, examples, AI contract, history, and review evidence are current.

---

## 40. Failure Conditions

RFDS-004 shall fail when:

- device protocol code directly calls a backend library without an approved adapter;
- a backend changes outbound or inbound bytes without declared codec or framing behavior;
- a read, write, open, or close operation can block indefinitely;
- a transaction can interleave with another operation;
- a write is replayed after uncertain completion without explicit safe-replay approval;
- backend exceptions leak as the only public error contract;
- `is_open` reports a failed session as healthy;
- transport configuration changes silently while open;
- USB selection is ambiguous;
- serial control lines change without declared policy;
- TCP packet boundaries are treated as protocol message boundaries;
- a zero-length TCP receive is treated as a valid empty response;
- a direct USB interface or kernel driver is not restored or released as documented;
- failed open leaves handles, locks, workers, or interfaces allocated;
- trace observation cannot prove the actual transport operation;
- trace data exposes secrets;
- unsupported backend features silently behave as successful no-ops;
- required simulator or backend contract tests are missing;
- mandatory documentation is not updated with a transport behavior change.

---

## 41. Review Checklist

1. Is the canonical boundary byte oriented?
2. Is protocol logic independent from the backend library?
3. Are state transitions explicit and tested?
4. Are all timeouts bounded and monotonic?
5. Is every read bounded by a terminator, length, backend message boundary, and maximum size?
6. Is transaction locking held across write and read?
7. Are unsafe retries prohibited?
8. Are uncertain writes reported accurately?
9. Are backend exceptions translated to stable errors?
10. Are resources released after successful close and failed open?
11. Is discovery separate from connection?
12. Is device selection deterministic?
13. Are serial DTR, RTS, and buffer policies explicit?
14. Does TCP handling respect stream semantics?
15. Is TLS verification safe by default when used?
16. Are USB interfaces, endpoints, and kernel-driver policies explicit?
17. Can a simulator reproduce partial reads, delays, timeouts, and disconnects?
18. Can a trace observer prove exact outbound and inbound operations?
19. Are trace payloads bounded and redacted?
20. Does the implementation pass the shared transport contract suite?
21. Are RFDS-017, RFDS-018, and RFDS-019 artifacts updated as required?
22. Are README, GitHub Pages, examples, guide, history, and review files current?

---

## 42. Minimum Definition of Done

RFDS-004 implementation is complete for a driver when:

- the base transport interface, data models, and error model are implemented;
- every declared backend is functional rather than a placeholder;
- configuration validation is complete;
- open, close, write, read, transact, and flush behavior is tested;
- state, timeout, locking, retry, disconnect, and cleanup tests pass;
- simulator and trace observer are available;
- RFDS-019 can capture protocol-boundary evidence;
- at least one approved physical or loopback integration profile passes for each supported backend type;
- documentation and connection examples are complete;
- AI contract and bench integration fields are updated;
- no Critical review findings remain;
- all Major findings are resolved or formally accepted with mitigation;
- release evidence is stored in `history/` and `review/`.

---

## 43. Goal

Provide one stable, safe, observable, and replaceable communication boundary so that RFDS instrument protocols and Robot Framework keywords behave consistently across VISA, serial, TCP/IP, direct USB, and deterministic simulator environments.

---

## Appendix A — Recommended Stable Error Codes

| Code | Meaning |
|---|---|
| `TR_CONFIG_INVALID` | Transport configuration is invalid |
| `TR_BACKEND_UNAVAILABLE` | Required backend is not installed or cannot initialize |
| `TR_DEVICE_NOT_FOUND` | No matching endpoint exists |
| `TR_DEVICE_AMBIGUOUS` | More than one endpoint matches |
| `TR_PERMISSION_DENIED` | Operating-system or backend permission denied |
| `TR_RESOURCE_BUSY` | Endpoint is already locked or in use |
| `TR_STATE_INVALID` | Operation is invalid in the current state |
| `TR_OPEN_FAILED` | Session open failed |
| `TR_OPEN_TIMEOUT` | Session open timed out |
| `TR_CLOSE_FAILED` | Session close failed |
| `TR_CLOSE_TIMEOUT` | Session close timed out |
| `TR_WRITE_FAILED` | Write failed |
| `TR_WRITE_TIMEOUT` | Write timed out |
| `TR_READ_FAILED` | Read failed |
| `TR_READ_TIMEOUT` | Read timed out |
| `TR_TRANSACTION_TIMEOUT` | Complete transaction timed out |
| `TR_SHORT_WRITE` | Fewer bytes were accepted than required |
| `TR_SHORT_READ` | Fewer bytes were received than required |
| `TR_RESPONSE_TOO_LARGE` | Response exceeded configured maximum |
| `TR_DISCONNECTED` | Endpoint disconnected or session became invalid |
| `TR_CAPABILITY_UNAVAILABLE` | Requested optional capability is unavailable |
| `TR_LOCK_TIMEOUT` | Resource or session lock could not be acquired in time |
| `TR_TRACE_FAILED` | Required trace evidence could not be recorded |
| `TR_INTERNAL_ERROR` | Unexpected transport implementation failure |

---

## Appendix B — Recommended Trace Record Example

```json
{
  "timestamp_utc": "2026-07-26T10:15:30.123456Z",
  "sequence": 42,
  "session_id": "tr-9f81c2",
  "transaction_id": "tx-00017",
  "operation_id": "Get Identity",
  "transport": "tcp",
  "endpoint": "192.168.0.55:5025",
  "event": "write_complete",
  "direction": "outbound",
  "byte_count": 6,
  "payload_mode": "hex_preview",
  "payload": "2a49444e3f0a",
  "duration_ms": 0.42,
  "status": "PASS"
}
```

---

## Appendix C — Required Backend Support Declaration

Each driver shall publish a table equivalent to:

| Backend | Supported | Tested profile | Limitations |
|---|---:|---|---|
| VISA | Yes/No | simulator / loopback / real device | Driver-specific |
| Serial | Yes/No | simulator / loopback / real device | Driver-specific |
| Raw TCP/IP | Yes/No | simulator / loopback / real device | Driver-specific |
| Direct USB | Yes/No | simulator / loopback / real device | Driver-specific |

A transport shall not be advertised as supported solely because a configuration field or empty backend module exists.
