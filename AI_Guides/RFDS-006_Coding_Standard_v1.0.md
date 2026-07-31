# RFDS-006 — Coding Standard

**Version:** 1.0  
**Document ID:** RFDS-006  
**Status:** Project requirement  
**Applies to:** All Python code in RFDS Robot Framework driver packages

---

## 1. Purpose

This specification defines the mandatory coding standard for Python-based Robot Framework drivers developed under RFDS.

It establishes enforceable requirements for:

- Python source style and formatting;
- module and package organization;
- public API design;
- type annotations and static analysis;
- docstrings and developer documentation;
- Robot Framework keyword implementation;
- logging and diagnostic evidence;
- exceptions and error reporting;
- configuration and secret handling;
- transport-facing code;
- maintainability, reviewability, and release evidence.

The objective is to make every RFDS driver consistent, understandable, testable, diagnosable, and safe to extend by both human developers and AI implementation agents.

---

## 2. Scope

### 2.1 In scope

RFDS-006 applies to:

- driver library source code;
- Robot Framework library adapters and keyword methods;
- transport implementations;
- parsers, serializers, protocol codecs, and data models;
- command-line utilities shipped with a driver;
- simulator and test-support Python code;
- example helper scripts;
- package build and quality-tool configuration;
- source-level documentation and logging behaviour.

### 2.2 Out of scope

RFDS-006 does not define:

- the mandatory Robot Framework keyword set;
- transport architecture and supported connection types;
- repository and release package layout;
- package version numbering;
- complete test coverage requirements;
- protocol conformance vectors;
- AI driver contract schema;
- test-bench topology;
- device-specific electrical safety limits.

Those subjects are defined by the applicable RFDS API, transport, package, test, and AI-contract specifications.

---

## 3. Normative Terminology

- **shall / shall not** — mandatory requirement;
- **should / should not** — recommended requirement; deviations require written justification;
- **may** — permitted implementation choice;
- **public API** — exported Python classes, functions, methods, properties, exceptions, constants, and Robot Framework keywords intended for external use;
- **internal API** — implementation detail not intended for external callers;
- **device-facing operation** — an operation that can cause transport I/O, a vendor SDK call, or a physical device state change.

---

## 4. Governing Principles

All RFDS Python code shall follow these principles:

1. **Clarity before compactness** — code shall favour explicit, readable behaviour over clever or compressed constructs.
2. **Typed boundaries** — public interfaces, configuration objects, protocol records, and returned results shall have explicit types.
3. **Deterministic behaviour** — inputs, outputs, timeouts, retries, side effects, and failure modes shall be documented and testable.
4. **Separation of concerns** — Robot Framework adaptation, domain logic, transport I/O, protocol serialization, and configuration shall not be unnecessarily coupled.
5. **No silent failure** — failures shall either be handled deliberately or propagated with actionable context.
6. **Evidence-preserving diagnostics** — significant operations shall produce useful logs without exposing secrets.
7. **Backward-aware evolution** — public API changes shall be deliberate, documented, and reflected in tests and contracts.
8. **Hardware-safe defaults** — default values shall not cause unsafe, destructive, or unexpectedly state-changing device operations.

---

## 5. Python Language Baseline

### 5.1 Supported Python versions

Each driver shall declare its supported Python versions in `pyproject.toml` using `requires-python`.

Unless a documented vendor SDK constraint prevents it:

- the minimum supported version should be Python 3.10 or newer;
- the driver shall be tested on the lowest declared supported version;
- the driver shall be tested on the highest version claimed by the release.

A driver shall not rely on an undeclared interpreter version or implementation-specific behaviour.

### 5.2 Source encoding and line endings

- Source files shall use UTF-8.
- Repository text files shall use LF line endings unless a platform-specific script requires otherwise.
- Python source files shall end with exactly one newline.
- Tabs shall not be used for Python indentation.

### 5.3 Future annotations

Modules that benefit from forward references should use:

```python
from __future__ import annotations
```

The choice shall be consistent within the production package.

---

## 6. Formatting and Style

### 6.1 Base style

Python code shall conform to PEP 8 except where this specification or the configured formatter defines a more specific rule.

### 6.2 Automated formatting

The project shall use one deterministic formatter configured in `pyproject.toml`.

The recommended RFDS default is Ruff format with:

```toml
[tool.ruff]
line-length = 100

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "lf"
```

An established package may use Black instead, but shall not mix competing formatters in the same package.

Formatting shall be automatic. Review comments shall not be used as a substitute for formatter enforcement.

### 6.3 Linting

The project shall use Ruff or an equivalent deterministic linter.

The linter configuration shall check, at minimum:

- syntax and undefined names;
- unused imports and variables;
- import order;
- common bug patterns;
- exception misuse;
- unsafe mutable defaults;
- unnecessary complexity indicators;
- invalid or missing docstring structure where configured;
- prohibited debug statements.

The release branch shall contain no unexplained linter errors.

A suppression shall:

- be as narrow as possible;
- include the exact rule identifier;
- be accompanied by a brief reason when the reason is not obvious;
- not suppress an entire file when a line- or symbol-level suppression is sufficient.

Example:

```python
result = sdk.read_raw()  # noqa: S307 — vendor SDK returns a trusted local expression
```

Broad `# noqa`, `# type: ignore`, and blanket exclusion patterns are prohibited without review justification.

### 6.4 Imports

Imports shall be grouped in this order:

1. Python standard library;
2. third-party packages;
3. RFDS shared packages;
4. local package imports.

Additional rules:

- absolute imports shall be used for production package code unless a relative import materially improves clarity;
- wildcard imports are prohibited;
- optional dependencies shall be imported behind an explicit capability boundary with an actionable error message;
- imports shall not perform device I/O or other material side effects.

### 6.5 Naming

The following conventions are mandatory:

| Element | Convention | Example |
|---|---|---|
| Module | `snake_case` | `serial_transport.py` |
| Package | `snake_case` | `rf_keysight34970` |
| Function or method | `snake_case` | `measure_dc_voltage` |
| Local variable | `snake_case` | `timeout_s` |
| Class | `PascalCase` | `VisaTransport` |
| Exception class | `PascalCase` ending in `Error` | `ProtocolResponseError` |
| Constant | `UPPER_SNAKE_CASE` | `DEFAULT_TIMEOUT_S` |
| Type alias | `PascalCase` | `ChannelIdentifier` |
| Private member | leading underscore | `_parse_response` |
| Robot keyword | readable title generated or declared from public method | `Measure DC Voltage` |

Names shall describe domain meaning. Single-letter names are permitted only for conventional short-loop indices, coordinates, or mathematical expressions with local scope.

Ambiguous abbreviations shall be avoided. Common protocol abbreviations such as SCPI, VISA, TCP, USB, DMM, PSU, and DUT may be used consistently.

### 6.6 Function size and complexity

A function or method shall perform one coherent responsibility.

As review thresholds:

- functions longer than approximately 50 logical lines should be decomposed;
- cyclomatic complexity above 10 should be justified or reduced;
- nesting deeper than four levels should be refactored;
- more than five independently meaningful parameters should normally be represented by a typed configuration or request object.

These thresholds are review triggers, not permission to create unreadable code below the threshold.

### 6.7 Expressions and control flow

Code shall:

- prefer guard clauses over deeply nested branches;
- avoid chained side effects in expressions;
- avoid assignment expressions where they reduce readability;
- use explicit comparison for sentinel values;
- use `is None` and `is not None` for `None` checks;
- avoid mutable default arguments;
- avoid catching `BaseException`;
- avoid bare `except:` clauses;
- avoid `assert` for runtime input validation or device safety checks.

---

## 7. Module and Package Design

### 7.1 Layer separation

Production drivers should separate these responsibilities:

```text
Robot Framework adapter / public library
                ↓
domain service and validation
                ↓
protocol command builder and response parser
                ↓
transport abstraction
                ↓
VISA / serial / TCP / HTTP / SDK implementation
```

A package may combine layers only when the driver is sufficiently small and the combined design remains testable and unambiguous.

### 7.2 Side effects

Module import shall not:

- open a transport;
- discover devices;
- create threads;
- modify global logging configuration;
- write files;
- read operator secrets;
- change device state.

Device communication shall begin only through an explicit public operation such as `open`, `connect`, or an intentionally documented auto-connect policy.

### 7.3 Global state

Mutable module-level global state is prohibited except for:

- immutable constants;
- cache objects with explicit lifecycle and thread-safety documentation;
- logger instances created by `logging.getLogger(__name__)`.

A driver shall not depend on hidden singleton connection state unless the API specification explicitly requires a singleton library scope.

### 7.4 Data models

Structured configuration, protocol results, identity records, and measurement results should use typed models such as:

- `dataclasses.dataclass`;
- `typing.NamedTuple` for immutable tuple-compatible records;
- enums derived from `enum.Enum` or `enum.StrEnum` when supported;
- validated external-schema models when the dependency is justified.

Plain dictionaries may be used at serialization boundaries, but their required keys and value types shall be defined.

### 7.5 Constants and units

Physical quantities and timing values shall include units in the name when the type does not carry unit metadata.

Examples:

```python
DEFAULT_TIMEOUT_S = 5.0
settling_time_ms = 250
voltage_v = 12.0
current_a = 0.5
resistance_ohm = 1_000.0
```

A code path shall not silently mix milliseconds and seconds, or base units and engineering-prefix values.

---

## 8. Public API Design

### 8.1 Stability

Every public symbol shall be intentionally public.

The package shall define its public surface using one or more of:

- documented import paths;
- `__all__`;
- Libdoc-visible Robot Framework keyword exposure;
- generated API documentation.

Internal helpers shall use a leading underscore and shall not be documented as supported external API.

### 8.2 Signatures

Public functions and methods shall:

- use explicit, descriptive parameter names;
- avoid `*args` and `**kwargs` unless extension behaviour is documented and validated;
- define stable defaults;
- avoid mutable default values;
- define keyword-only parameters when this prevents argument-order mistakes;
- return a documented type on every normal path.

Example:

```python
def measure_dc_voltage(
    self,
    channel: int,
    *,
    range_v: float | None = None,
    resolution_v: float | None = None,
    timeout_s: float | None = None,
) -> float:
    """Measure DC voltage on one channel and return volts."""
```

### 8.3 Validation

Inputs shall be validated at the earliest layer that has sufficient semantic knowledge.

Validation errors shall:

- identify the invalid parameter;
- include the received value when safe;
- state the accepted range, type, or set;
- occur before transmission when the value is invalid independently of device state.

### 8.4 Return values

Public return values shall be:

- deterministic;
- documented;
- compatible with Robot Framework where exposed as keywords;
- free from open file handles, generators tied to live transports, or non-serializable implementation objects unless explicitly required.

Robot-facing results should use:

- `None` for command-only success;
- `bool`, `int`, `float`, or `str` for scalar values;
- lists or dictionaries with stable schemas;
- typed Python result objects only when Robot Framework compatibility and documentation are proven.

### 8.5 Deprecation

A public API shall not be removed or incompatibly changed without:

- a documented deprecation period unless a critical safety defect requires immediate removal;
- a runtime warning or documented compatibility alias where practical;
- history and release-note entries;
- updated examples, tests, AI contract, and conformance vectors;
- an explicit migration path.

---

## 9. Type Annotation Standard

### 9.1 Mandatory coverage

Type annotations are mandatory for:

- all public functions and methods;
- all Robot Framework keyword methods;
- constructors of public classes;
- dataclass fields;
- protocol request and response models;
- transport interfaces;
- configuration structures;
- public constants whose inferred type is not obvious;
- callback signatures;
- variables initialized with `None` when the later type is not obvious.

Private functions should also be fully typed.

### 9.2 Static type checking

Each driver shall run one configured static type checker, normally mypy or Pyright.

The checker shall cover the production package and should cover test-support modules.

At minimum, the configuration shall detect:

- missing return paths;
- incompatible assignments;
- invalid argument types;
- invalid overrides;
- untyped public definitions;
- unsupported optional-value access;
- incorrect collection element types.

The release branch shall have no unexplained static type errors in production code.

### 9.3 `Any`

`Any` shall not be used as a default escape from type design.

It is permitted at boundaries that are genuinely dynamic, including:

- Robot Framework runtime metadata;
- vendor SDKs without usable type information;
- decoded JSON before validation;
- plugin interfaces whose schema is external.

Each material `Any` boundary shall be narrowed through validation, casting, a protocol, or a typed adapter before entering core domain logic.

### 9.4 Type ignores

`# type: ignore` shall include the specific error code when the type checker supports it.

Example:

```python
value = vendor.read()  # type: ignore[no-untyped-call]
```

A type-ignore comment shall not conceal an actual runtime defect.

### 9.5 Protocols and abstract interfaces

Transport and service interfaces should use `typing.Protocol` or an abstract base class where multiple implementations are expected.

Example:

```python
from typing import Protocol


class TextTransport(Protocol):
    def open(self) -> None: ...
    def close(self) -> None: ...
    def write(self, command: str) -> None: ...
    def query(self, command: str, *, timeout_s: float | None = None) -> str: ...
```

### 9.6 Optional values

Optional values shall be represented explicitly with `T | None` or `Optional[T]`.

Empty string, zero, `False`, and empty containers shall not be used as undocumented substitutes for missing data.

### 9.7 Numeric types

- Use `int` for integral protocol values and indices.
- Use `float` for ordinary measured or configured physical quantities unless decimal precision is contractually required.
- Use `Decimal` only when decimal arithmetic is required and consistently preserved across the API.
- Do not compare floating-point measurement values for exact equality unless the protocol guarantees exact representation.

---

## 10. Robot Framework Keyword Implementation

### 10.1 Keyword exposure

Robot Framework keywords shall be intentionally exposed through the selected library API mechanism.

A helper method shall not become a public Robot Framework keyword accidentally.

Where automatic keyword discovery is used, internal methods shall be private or excluded using the supported Robot Framework API.

### 10.2 Keyword naming

Keyword names shall:

- be readable in Robot Framework test cases;
- remain consistent across RFDS drivers for equivalent operations;
- avoid device-model-specific wording when a common canonical term exists;
- preserve approved aliases when backward compatibility requires them.

Python method names shall remain valid `snake_case` identifiers.

### 10.3 Keyword documentation

Every public keyword shall document:

- purpose;
- argument meaning, accepted values, and units;
- preconditions;
- device state changes and side effects;
- return value and type;
- relevant timeout behaviour;
- important exceptions or Robot Framework failures;
- safety constraints;
- a short Robot Framework usage example when the call is not self-evident.

Keyword documentation shall remain compatible with Robot Framework Libdoc generation.

### 10.4 Robot Framework failures

Device and validation failures shall reach Robot Framework as clear failures with actionable messages.

Messages shall not expose an internal traceback as the only explanation.

The original exception shall be preserved through exception chaining when a higher-level exception is raised.

### 10.5 Logging from keywords

Keyword implementation shall not use `print()` for normal diagnostics.

Robot-specific log output may use `robot.api.logger` in the Robot adapter layer. Core and transport layers shall use the Python logging standard described in Section 12.

### 10.6 Keyword aliases

Aliases shall:

- call the same canonical implementation;
- produce equivalent protocol behaviour unless explicitly documented otherwise;
- be marked as aliases in documentation and AI contracts;
- be included in conformance inventory and tests.

---

## 11. Documentation and Docstrings

### 11.1 Documentation language

Project documentation and source docstrings shall use clear technical English.

Device protocol tokens, vendor terms, error messages, and registered product names shall preserve their correct spelling and case.

### 11.2 Required module documentation

Each production module shall contain a module docstring that states:

- the module responsibility;
- important boundaries or side effects;
- relevant protocol or layer context where not obvious.

A module docstring shall not merely repeat the filename.

### 11.3 Required public docstrings

Docstrings are mandatory for:

- public modules;
- public classes;
- public functions and methods;
- public exceptions;
- public data models whose fields are not self-explanatory;
- Robot Framework keyword methods.

Private symbols shall be documented when their behaviour, algorithm, side effects, or constraints are non-trivial.

### 11.4 Docstring format

A package shall use one consistent structured docstring style. Google style is the recommended RFDS default.

Example:

```python
def set_output_voltage(
    self,
    channel: int,
    voltage_v: float,
    *,
    timeout_s: float | None = None,
) -> None:
    """Set the programmed output voltage for one channel.

    Args:
        channel: One-based output channel number.
        voltage_v: Requested voltage in volts.
        timeout_s: Optional operation timeout in seconds. Uses the connection
            default when omitted.

    Raises:
        DriverNotConnectedError: If no transport session is open.
        InvalidArgumentError: If the channel or voltage is outside the
            driver-declared range.
        DeviceProtocolError: If the instrument reports a command error.

    Side Effects:
        Changes the programmed voltage of the selected hardware output.

    Robot Framework Example:
        | Set Output Voltage | 1 | 5.0 |
    """
```

The exact section labels may be adapted for Libdoc readability, but the semantic content shall remain.

### 11.5 Comments

Comments shall explain **why**, constraints, protocol quirks, safety reasoning, or non-obvious decisions.

Comments shall not restate obvious code.

Temporary work markers such as `TODO`, `FIXME`, and `HACK` shall include:

- an issue or requirement reference;
- a concise reason;
- the intended resolution condition.

Example:

```python
# TODO(RFDS-123): Remove compatibility branch after vendor SDK 5.x is no longer supported.
```

Untracked temporary markers shall fail release review.

### 11.6 Protocol references

Non-obvious command construction, binary fields, checksums, timing rules, and response parsing should cite the relevant vendor manual section, protocol command, or internal requirement identifier in a comment or nearby documentation.

### 11.7 Examples in documentation

Documentation examples shall:

- use current public keyword names and signatures;
- avoid real credentials and private network information;
- identify required hardware state;
- be executable or verified where practical;
- be updated in the same revision as an API change.

---

## 12. Logging Standard

### 12.1 Logging framework

Production code shall use the Python standard `logging` package.

Each module shall declare:

```python
import logging

logger = logging.getLogger(__name__)
```

Library modules shall not call `logging.basicConfig()` and shall not replace application-level handlers.

### 12.2 Log levels

The following level policy is mandatory:

| Level | Required use |
|---|---|
| `DEBUG` | Detailed internal state, protocol construction, parsed fields, retry decisions, and trace information useful to developers |
| `INFO` | Significant lifecycle events such as connection established, identity confirmed, configuration loaded, or controlled shutdown |
| `WARNING` | Recoverable abnormal conditions, fallback behaviour, deprecation, retry, partial capability, or operator-relevant risk |
| `ERROR` | Operation failed and the current request cannot complete, but the process or library remains usable |
| `CRITICAL` | Unsafe state, unrecoverable initialization failure, corrupted mandatory configuration, or condition requiring immediate operator intervention |

Routine successful measurements shall not flood `INFO` unless the driver specification explicitly requires audit-level measurement logging.

This table uses the Python standard-library `logging` level names (including `WARNING`) because it governs calls into that module. It is distinct from the RFDS-008 §28.1 evidence-level vocabulary (`TRACE`/`DEBUG`/`INFO`/`WARN`/`ERROR`/`CRITICAL`) used for structured evidence records; a `logger.warning(...)` call should be mapped to RFDS-008's `WARN` evidence level when the message is also captured as structured evidence.

### 12.3 Log message content

A diagnostic log should include applicable context such as:

- driver and transport instance;
- operation or keyword;
- device resource or redacted address;
- channel or subsystem;
- timeout;
- attempt number;
- protocol vector or request identifier;
- duration;
- result category;
- device error code.

Messages shall be concise, grammatically clear, and useful without reading the source line.

Preferred:

```python
logger.warning(
    "SCPI query timed out; resource=%s command=%r timeout_s=%.3f attempt=%d/%d",
    resource,
    command,
    timeout_s,
    attempt,
    max_attempts,
)
```

Avoid:

```python
logger.warning(f"Error {e}")
```

Lazy formatting with `%s` placeholders shall be used for ordinary logging calls.

### 12.4 Protocol logging

Outbound and inbound protocol data may be logged at `DEBUG` or a dedicated trace mechanism.

Protocol logs shall:

- distinguish transmit and receive directions;
- preserve ordering;
- identify the operation that generated the exchange;
- make control characters or binary data unambiguous;
- truncate extremely large payloads using a documented limit;
- state when truncation occurred;
- redact credentials, tokens, private keys, and other secrets.

Example text trace:

```text
TX resource=TCPIP0::192.0.2.10::5025::SOCKET command='MEAS:VOLT? (@1)\n'
RX resource=TCPIP0::192.0.2.10::5025::SOCKET response='5.0012\n' duration_ms=18.4
```

### 12.5 Sensitive data

The following shall never appear unredacted in logs, exceptions, reports, or screenshots:

- passwords;
- API tokens;
- private keys;
- session cookies;
- authentication headers;
- credentials embedded in URLs;
- operator personal data not required for the test record.

A value shall be redacted before it reaches the logging call.

### 12.6 Exceptions and stack traces in logs

- Use `logger.exception(...)` only while handling an active exception and when a stack trace is diagnostically justified.
- Do not log the same exception at multiple layers unless each layer adds distinct context.
- A layer that cannot resolve an error should normally add context through exception chaining and let the boundary layer decide how to log it.

### 12.7 Robot Framework log bridge

When a driver exposes logs through Robot Framework:

- the bridge shall preserve the original severity where practical;
- the bridge shall not duplicate every message into both Python and Robot logs;
- protocol trace output should be optional and disabled by default at normal log levels;
- logging configuration shall not change globally merely because the library was imported.

---

## 13. Exception and Error-Handling Standard

### 13.1 Exception hierarchy

RFDS-007 is the sole normative source for the RFDS exception hierarchy, class names, and error codes. Each driver package shall expose the RFDS-007 base exception:

```python
class DriverError(Exception):
    """Base exception for all expected driver failures."""
```

Specific exceptions shall derive from `DriverError` using the RFDS-007 category names (for example `DriverConfigurationError`, `DriverValidationError`, `DriverStateError`, `DriverConnectionError`, `DriverTransportError` with `DriverTimeoutError` beneath it, `DriverProtocolError`, `DriverDeviceError`, `DriverResourceError`, `DriverSafetyError`, `DriverDependencyError`, `DriverInternalError`). A driver may add narrower subclasses beneath these categories but shall not introduce a parallel, differently-named top-level taxonomy.

### 13.2 Exception messages

Exception messages shall:

- state what failed;
- identify the affected operation;
- include relevant safe context;
- state the immediate cause when known;
- avoid vague text such as `Failed`, `Unknown error`, or `Something went wrong` without context.

### 13.3 Exception chaining

When converting a lower-level exception, use explicit chaining:

```python
try:
    response = self._transport.query(command, timeout_s=timeout_s)
except TimeoutError as exc:
    raise DriverTimeoutError(
        f"Identity query timed out after {timeout_s:.3f} s"
    ) from exc
```

Use `from None` only when hiding the lower-level context is intentional and justified for the user-facing boundary.

### 13.4 Recovery

An exception handler shall not claim successful recovery unless the recovered state is verified.

After a recoverable transport or protocol failure, the driver shall either:

- restore a documented usable state;
- reconnect explicitly;
- mark the session disconnected and require a new connection;
- raise an exception that clearly states the resulting state.

### 13.5 Cleanup

Resources shall be closed with deterministic cleanup using:

- context managers;
- `try` / `finally`;
- explicit idempotent `close` or `disconnect` methods.

Cleanup errors shall not silently replace the original operation error. Where both matter, the original error shall remain primary and cleanup failure shall be logged or attached with clear context.

### 13.6 Prohibited error handling

The following are prohibited:

- bare `except:`;
- swallowing an exception without a documented recovery action;
- returning a fabricated success value after failure;
- converting all errors to one generic exception without preserving categories;
- using `assert` for user input, protocol validity, connection state, or safety enforcement;
- indefinite retry loops;
- retries without timeout or attempt limits;
- retrying non-idempotent state-changing operations without explicit safety analysis.

---

## 14. Transport and Protocol Code

### 14.1 Explicit timeouts

Every blocking device-facing operation shall have an effective timeout.

The timeout may come from:

- an explicit keyword argument;
- connection configuration;
- a documented operation-specific default.

An operation shall not block indefinitely because a timeout was omitted.

### 14.2 Command construction

Protocol commands and frames shall be built in dedicated, testable code when construction is non-trivial.

Construction code shall clearly define:

- encoding;
- terminator;
- byte order;
- addressing;
- length fields;
- checksum or integrity fields;
- numeric formatting;
- enum mapping;
- escaping or quoting rules.

String concatenation distributed across public keyword methods is prohibited when it obscures protocol behaviour.

### 14.3 Parsing

Response parsing shall:

- validate framing before extracting data;
- reject incomplete or malformed responses;
- validate required fields;
- preserve raw response evidence when useful;
- convert to documented units and types explicitly;
- distinguish transport failure from device-reported error and parse failure.

### 14.4 Text encoding

Text protocols shall declare their encoding. ASCII shall be used only where the protocol specifies or guarantees ASCII.

Encoding and decoding failures shall raise a documented protocol exception with the raw-data context represented safely.

### 14.5 Retries

Retries shall be:

- bounded by count and overall time;
- limited to documented recoverable conditions;
- logged at `WARNING` or `DEBUG` according to operational significance;
- safe for the operation being repeated;
- followed by a final exception that states the number of attempts.

### 14.6 Thread safety and concurrency

A driver shall explicitly document whether one library instance is thread-safe.

Where concurrent access is unsupported, the implementation should fail predictably or serialize access rather than allowing interleaved protocol frames.

Locks shall:

- protect the smallest coherent critical section;
- not be held during unrelated computation;
- have documented ordering when more than one lock exists;
- not create unbounded deadlock risk.

### 14.7 Cancellation and stop behaviour

Long-running operations should expose a bounded stop or cancellation path where the underlying protocol permits it.

Stop handling shall leave the device and transport in a documented state and shall not merely abandon a worker thread that continues device I/O.

---

## 15. Configuration and Secrets

### 15.1 Configuration models

Connection and driver configuration shall use a documented, typed representation.

Configuration precedence shall be explicit when values may come from multiple sources such as:

1. direct keyword or constructor arguments;
2. profile file;
3. environment variable;
4. package default.

### 15.2 Defaults

Defaults shall be:

- safe;
- documented;
- consistent across code, examples, README, guide, and AI contract;
- defined in one authoritative location where practical.

### 15.3 Secrets

Secrets shall not be:

- committed to the repository;
- embedded in examples;
- stored in default configuration files;
- included in protocol traces;
- returned by `repr()` of configuration objects.

Secret-bearing fields shall use redacted representations.

### 15.4 File handling

Configuration and result files shall:

- use explicit encodings;
- use context managers;
- validate schema before use;
- report the file path and validation issue on failure;
- avoid partial overwrite through atomic replacement when corruption would be consequential.

---

## 16. Logging, Representation, and Diagnostic Safety

### 16.1 `repr()`

Custom `__repr__` implementations shall:

- be unambiguous;
- avoid live device I/O;
- redact secrets;
- avoid dumping very large buffers;
- not raise under normal object states.

### 16.2 Device identity

Logs and reports may include device manufacturer, model, serial number, firmware version, and resource address when required for traceability.

Sensitive bench identifiers or credentials shall be redacted according to project policy.

### 16.3 Binary data

Binary frames shall be logged using a deterministic representation such as hexadecimal bytes.

Example:

```text
TX frame_hex=AA 00 20 00 00 00 00 00 ... checksum=CA
```

Large frames shall include original length and truncation status.

---

## 17. Testability Requirements

### 17.1 Dependency injection

Transport and clock dependencies should be injectable where this enables deterministic testing.

Device-facing core logic shall not require a physical device for all unit tests.

### 17.2 Time and sleep

Direct calls to `time.sleep()` shall be limited to code where actual wall-clock delay is the intended behaviour.

Long or repeated waits should use an injectable sleeper, polling helper, deadline abstraction, or equivalent testable mechanism.

### 17.3 Randomness

Random behaviour shall not affect protocol or test outcomes unless explicitly required.

When randomness is used in simulators or tests, the seed shall be controllable and recorded.

### 17.4 Deterministic tests

Tests shall not depend on:

- execution order unless declared;
- developer-local absolute paths;
- uncontrolled network access;
- current locale;
- current wall-clock time without a controlled clock;
- previously connected device state without setup.

### 17.5 Test code quality

Test code shall follow the same fundamental readability, typing, logging, and error-handling rules as production code, with reasonable exceptions for concise fixtures and parameterization.

---

## 18. Tooling and `pyproject.toml`

Each package shall configure its quality tools in `pyproject.toml` or in clearly referenced project configuration files.

The configuration shall define, as applicable:

- build system;
- package metadata;
- supported Python versions;
- runtime dependencies;
- optional development and documentation dependencies;
- formatter settings;
- linter settings;
- static type-checker settings;
- pytest settings;
- coverage settings;
- documentation build settings.

Recommended minimum quality commands:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy rf_<driver_name>
python -m pytest
```

Equivalent commands may be used when the package has approved alternative tools.

Tool versions shall be reproducible through a lock file, constraints file, or pinned development environment definition.

---

## 19. Prohibited Practices

The following practices are prohibited in released production code unless an approved exception is recorded:

- `print()` for library diagnostics;
- wildcard imports;
- import-time device communication;
- mutable default arguments;
- bare exceptions;
- empty exception handlers;
- unbounded retry loops;
- blocking calls without an effective timeout;
- `eval()` or `exec()` on external or device-supplied data;
- hard-coded credentials;
- hard-coded developer-local absolute paths;
- silent unit conversion;
- undocumented global mutable state;
- public methods without type annotations;
- public keywords without user-facing documentation;
- broad `# noqa` or `# type: ignore` suppression without justification;
- commented-out production code retained as history;
- unreachable compatibility branches with no deprecation plan;
- duplicate protocol command construction across multiple methods where one canonical builder is practical;
- returning success after a device or transport error;
- logging secrets or authentication material;
- modifying root logging configuration from an imported library;
- using assertions for runtime safety or validation;
- indefinite worker threads that prevent clean process shutdown.

---

## 20. Required Quality Evidence

Each gate or release that modifies Python code shall record the following evidence in the applicable `review/` entry or generated quality report:

| Check | Required evidence |
|---|---|
| Formatting | Formatter check command and PASS result |
| Linting | Linter command, configuration, and PASS result |
| Static typing | Type-check command and PASS result or approved findings |
| Unit and integration tests | Test command and summarized result |
| Public API review | Added, changed, deprecated, and removed public symbols |
| Keyword documentation | Libdoc generation result or equivalent validation |
| Logging review | Confirmation of levels, redaction, and no `print()` diagnostics |
| Exception review | Error hierarchy and failure-message review |
| Security review | Secret scan or equivalent repository check |
| Compatibility review | Supported Python versions and dependency compatibility |

A PASS claim shall identify the command, tool version, and revision tested.

---

## 21. Gate Integration

RFDS lifecycle gates shall apply RFDS-006 as follows.

### 21.1 Gate 1 — Architecture and Skeleton

Required:

- package imports successfully;
- formatter, linter, and type-check configuration exists;
- public interfaces are typed;
- module boundaries and exception hierarchy are defined;
- no Critical coding-standard finding remains.

### 21.2 Gate 2 — Core Implementation

Required:

- implemented public methods are typed and documented;
- validation and error handling are present;
- no uncontrolled print diagnostics exist;
- core unit tests pass;
- device-facing operations have bounded timeouts.

### 21.3 Gate 3 — Extended Features

Required:

- new features preserve architecture and API consistency;
- edge cases and retries follow this standard;
- AI contract and keyword documentation remain synchronized;
- no unjustified complexity increase remains.

### 21.4 Gate 4 — Tests and Documentation

Required:

- full quality-tool suite passes;
- public documentation and examples reflect current signatures;
- log and error paths are tested;
- static type checking passes for production code;
- Libdoc output is generated successfully.

### 21.5 Gate 5 — Review and Release

Required:

- no Critical or Major RFDS-006 findings remain unresolved;
- any approved deviations are listed with owner and rationale;
- quality evidence is stored in `review/`;
- coding changes are described in `history/`;
- release documentation uses the final public API.

---

## 22. Review Severity

Coding-standard findings shall use these severities:

### Critical

A defect that may cause:

- unsafe hardware behaviour;
- secret disclosure;
- uncontrolled or indefinite device operation;
- corrupt protocol output with significant risk;
- silent false success;
- unrecoverable package import or startup failure.

Critical findings block every gate and release.

### Major

A defect that materially affects:

- public API correctness;
- error classification;
- timeout behaviour;
- type safety at a public boundary;
- testability;
- protocol traceability;
- maintainability of a significant feature.

Major findings block phase completion and release unless an explicit approved deviation exists.

### Minor

A localized maintainability, clarity, documentation, or consistency issue that does not materially change behaviour.

Minor findings should be fixed in the current gate or tracked with a specific follow-up reference.

### Observation

A non-blocking improvement or future refactoring opportunity.

---

## 23. Approved Deviations

A deviation from RFDS-006 shall be recorded in the gate review and include:

- requirement identifier or section;
- affected files and symbols;
- technical reason;
- risk assessment;
- compensating control;
- owner;
- expiry condition or review date.

A vendor SDK limitation alone is not sufficient justification unless the driver isolates the limitation behind a typed and documented adapter.

---

## 24. Change Control

Whenever a code change adds, removes, renames, aliases, deprecates, or changes a public API or device-facing behaviour, the same revision shall update all applicable artifacts:

- type annotations;
- docstrings and Libdoc content;
- unit and integration tests;
- Robot Framework examples;
- README and user guide;
- AI driver contract under RFDS-017;
- protocol conformance vectors under RFDS-019;
- history entry;
- code review entry.

A public API change without synchronized documentation and verification shall fail review.

---

## 25. Review Checklist

1. Does every production module have one clear responsibility?
2. Are public APIs intentionally exposed and stable?
3. Are all public methods and keywords fully typed?
4. Does static type checking pass without unexplained ignores?
5. Does automated formatting pass?
6. Does linting pass without broad suppressions?
7. Are names explicit, consistent, and unit-aware?
8. Are mutable defaults, hidden globals, and import-time side effects absent?
9. Are Robot Framework keywords documented for arguments, units, side effects, returns, errors, timing, and safety?
10. Are protocol commands built and parsed in testable code?
11. Does every blocking operation have an effective timeout?
12. Are retries bounded, safe, and observable?
13. Is the exception hierarchy meaningful and consistently used?
14. Are exception messages actionable and chained to original causes?
15. Are logs emitted at appropriate levels?
16. Are protocol traces directional, attributable, and safely redacted?
17. Does library code avoid changing global logging configuration?
18. Are credentials and secrets absent from source, examples, logs, and errors?
19. Are cleanup and disconnect operations deterministic and idempotent?
20. Is concurrency behaviour documented and protected?
21. Are examples and documentation synchronized with the current API?
22. Are quality commands and tool versions recorded in review evidence?
23. Are all Critical and Major findings resolved or formally approved?
24. Are RFDS-017 and RFDS-019 artifacts updated when public calls change?
25. Is the implementation understandable without relying on undocumented developer knowledge?

---

## 26. Minimum Definition of Done

A Python code revision satisfies RFDS-006 when:

- production code is automatically formatted;
- linting passes;
- static type checking passes for production code;
- all public APIs and Robot Framework keywords are typed and documented;
- no prohibited practice remains;
- all device-facing operations have bounded timeout behaviour;
- exceptions are categorized, actionable, and preserve causes;
- logging uses the defined levels and redacts sensitive data;
- tests for changed behaviour pass;
- Libdoc generation succeeds for the Robot Framework library;
- public API, examples, AI contract, and conformance artifacts are synchronized;
- required quality evidence is stored in the gate or release review;
- no unresolved Critical or Major coding-standard finding remains.

---

## 27. Goal

Provide a uniform, enforceable Python engineering standard so that every RFDS Robot Framework driver is readable, typed, documented, diagnosable, testable, hardware-safe, and maintainable across repeated revisions.

---

## Appendix A — Recommended `pyproject.toml` Baseline

This appendix is informative. A package may adapt it while preserving the mandatory requirements above.

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "rf-example"
version = "0.0.0"
requires-python = ">=3.10"
dependencies = [
  "robotframework>=6",
]

[project.optional-dependencies]
dev = [
  "mypy",
  "pytest",
  "pytest-cov",
  "ruff",
]

[tool.ruff]
line-length = 100
target-version = "py310"
src = ["rf_example", "tests"]

[tool.ruff.lint]
select = [
  "E",
  "F",
  "I",
  "B",
  "BLE",
  "C4",
  "DTZ",
  "G",
  "LOG",
  "PIE",
  "RET",
  "RUF",
  "S",
  "SIM",
  "T20",
  "UP",
]
[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101"] # Assertions are permitted in tests only.

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "lf"

[tool.mypy]
python_version = "3.10"
strict = true
warn_unused_ignores = true
warn_redundant_casts = true
warn_unreachable = true
show_error_codes = true

[tool.pytest.ini_options]
addopts = "-ra --strict-config --strict-markers"
testpaths = ["tests"]

[tool.coverage.run]
branch = true
source = ["rf_example"]

[tool.coverage.report]
show_missing = true
skip_covered = false
```

---

## Appendix B — Recommended Exception Pattern

This example follows the RFDS-007 category names; RFDS-007 remains the authoritative source for the complete hierarchy.

```python
from __future__ import annotations


class DriverError(Exception):
    """Base exception for expected driver failures."""


class DriverStateError(DriverError):
    """Raised when an operation requires a session state that is not current, e.g. no open connection."""


class DriverTransportError(DriverError):
    """Raised when the transport boundary fails."""


class DriverTimeoutError(DriverTransportError):
    """Raised when a device-facing operation exceeds its timeout."""


class DriverProtocolError(DriverError):
    """Raised when protocol exchange or parsing fails."""


class DriverDeviceError(DriverProtocolError):
    """Raised when the device reports an explicit protocol error."""
```

---

## Appendix C — Recommended Logging Pattern

```python
from __future__ import annotations

import logging
import time
from typing import Protocol

logger = logging.getLogger(__name__)


class TextTransport(Protocol):
    """Minimal text-query transport used by this example."""

    def query(self, command: str, *, timeout_s: float) -> str: ...


def query_identity(transport: TextTransport, *, timeout_s: float) -> str:
    """Query and return the device identity string."""
    command = "*IDN?"
    started = time.monotonic()

    logger.debug("Sending identity query; command=%r timeout_s=%.3f", command, timeout_s)

    try:
        response = transport.query(command, timeout_s=timeout_s)
    except TimeoutError as exc:
        logger.warning("Identity query timed out; timeout_s=%.3f", timeout_s)
        raise DriverTimeoutError(
            f"Identity query timed out after {timeout_s:.3f} s"
        ) from exc

    duration_ms = (time.monotonic() - started) * 1_000.0
    identity = response.strip()
    if not identity:
        raise DriverProtocolError("Identity query returned an empty response")

    logger.debug(
        "Identity query completed; duration_ms=%.1f response=%r",
        duration_ms,
        identity,
    )
    return identity
```
