> **Historical specification:** This file preserves the original design task. The archive and fixed-root names shown below were superseded by the project-wide convention `rf_votsch_climate_chamber_vYY.RR.zip` containing `rf_votsch_climate_chamber/`. See `PROJECT_REQUIREMENTS.md`.

# Task: Robot Framework Library Adapter for Vötsch Climate Chamber

## 1. Decision

Create a dedicated **Robot Framework adapter library** around the existing `ClimateChamber` Python driver.

Do not convert the driver itself into a Robot Framework library by adding keyword decorators directly to all public methods.

Before implementing the adapter, perform a focused review and small hardening pass on the driver. The driver must remain independently usable from normal Python code.

## 2. Rationale

The supplied driver already contains the main transport and instrument-domain responsibilities:

- TCP connection and reconnect handling
- command framing and parsing
- typed chamber exceptions
- temperature safety limits
- start/stop and digital output control
- setpoint write verification
- long-running temperature stabilization
- thread-safe operations
- health and communication statistics

A separate adapter is preferable because:

1. Robot Framework keywords require explicit, user-oriented actions, while the driver contains properties and low-level implementation methods.
2. The driver currently connects from its constructor. Robot library import should not unexpectedly open hardware connections.
3. Robot logging, argument conversion, suite lifecycle, teardown, assertions, and keyword naming are framework-specific concerns.
4. The driver should remain reusable by Python scripts, pytest, command-line tools, and other automation frameworks.
5. Explicit keyword exposure prevents internal methods such as socket handling and raw protocol functions from becoming accidental test keywords.
6. The adapter can evolve without breaking the stable driver API.

## 3. Project Goal

Deliver an installable Robot Framework library that provides safe, readable, documented keywords for controlling a Vötsch/SimServ-compatible climate chamber while reusing the supplied `ClimateChamber` driver.

Example intended usage:

```robot
*** Settings ***
Library           votsch_climate_chamber.robot_library.VotschClimateChamberLibrary
Suite Setup       Connect Climate Chamber
...               192.168.1.50
...               -40
...               180
Suite Teardown    Stop And Disconnect Climate Chamber

*** Test Cases ***
Run DUT At 85 Degrees
    Set Climate Chamber Temperature    85
    Start Climate Chamber
    Wait Until Climate Chamber Is Stable
    ...    target=85
    ...    tolerance=0.8
    ...    stable_samples=3
    ...    timeout=2h
    ${actual}=    Get Climate Chamber Temperature
    Should Be True    abs(${actual} - 85) <= 0.8
```

## 4. Target Compatibility

- Python: 3.10 or newer
- Robot Framework: 7.4.x baseline
- Operating systems: Windows and Linux
- Chamber protocol: TCP, default port 2049
- Existing Python driver API: remain backward compatible unless an issue is explicitly documented and approved

## 5. Proposed Repository Layout

Do not use a `src/` directory.

```text
robotframework-votsch-climate-chamber/
├── pyproject.toml
├── README.md
├── LICENSE
├── CHANGELOG.md
├── votsch_climate_chamber/
│   ├── __init__.py
│   ├── driver.py
│   ├── robot_library.py
│   ├── robot_logging.py
│   ├── errors.py
│   └── version.py
├── tests/
│   ├── unit/
│   ├── robot/
│   ├── integration/
│   └── hardware/
├── examples/
│   ├── basic_control.robot
│   ├── temperature_cycle.robot
│   ├── suite_setup_teardown.robot
│   └── variables.example.yaml
└── scripts/
    ├── run_unit_tests.ps1
    ├── run_unit_tests.sh
    ├── run_robot_tests.ps1
    ├── run_robot_tests.sh
    ├── build.ps1
    └── build.sh
```

The supplied file should initially be moved to `votsch_climate_chamber/driver.py` with its public API retained.

## 6. Architecture

### 6.1 Driver layer

The driver layer owns:

- TCP socket creation and closure
- protocol command creation
- response framing and parsing
- retries and reconnect behavior
- chamber-domain validation
- readback verification
- chamber state and measurements
- stabilization and dwell algorithms
- driver-specific exceptions

The driver layer must not import Robot Framework.

### 6.2 Robot adapter layer

The adapter layer owns:

- Robot keyword names and documentation
- Robot argument conversion
- connection lifecycle at suite level
- Robot logging
- user-friendly failure messages
- optional assertion keywords
- Robot time-string conversion
- safe teardown keywords
- intentional exposure of supported operations

The adapter must use composition:

```python
self._driver: ClimateChamber | None
```

It must not inherit from `ClimateChamber`.

### 6.3 Keyword exposure

Use:

```python
from robot.api.deco import keyword, library

@library(scope="SUITE", auto_keywords=False)
class VotschClimateChamberLibrary:
    ...
```

Only methods decorated with `@keyword` may be exposed.

Default library scope shall be `SUITE`, so one chamber session is reused by all tests in a suite and is isolated from other suites.

## 7. Required Driver Review Before Adapter Implementation

Perform a file-by-file review of the supplied driver and document findings by severity.

At minimum, review and test:

1. Constructor side effects and whether connection can be deferred.
2. Socket reconnect behavior after partial responses and disconnects.
3. Preservation of bytes received after the first protocol terminator.
4. Maximum response size enforcement after each received chunk.
5. Meaning of `is_connected`; distinguish “socket object exists” from verified communication.
6. Retry counters and whether one logical command can be counted consistently.
7. Behavior when `response_timeout`, `timeout`, retry count, or response size are invalid.
8. Logging of ANSI color sequences into Robot logs.
9. Interruption and cancellation behavior during long `set_and_wait()` operations.
10. Cleanup behavior after Robot execution is interrupted.
11. Thread locking during long stabilization and dwell operations.
12. Start/stop verification behavior on slow chambers.
13. Readback tolerance behavior and floating-point formatting.
14. Error messages for malformed or unexpected protocol responses.
15. Unit testability without real hardware.

### 7.1 Permitted targeted driver changes

The following backward-compatible changes are permitted:

- add `connect()` as an explicit public method
- add a keyword-only `connect_on_init: bool = True` constructor option
- add `verify_connection()` or `ping()` using a harmless chamber query
- add `wait_until_temperature(...)` as a reusable operation separate from setting and starting
- add an optional cancellation callback to long-running waits
- improve internal receive buffering
- validate all transport configuration values
- remove terminal color codes from structured log records
- add dependency injection for socket creation and clock/sleep functions for tests

Existing positional constructor arguments and existing public methods must continue to work.

## 8. Robot Library Initialization

The Robot library constructor must not connect to hardware.

Recommended constructor:

```python
def __init__(
    self,
    default_timeout: str = "1 second",
    default_response_timeout: str | None = None,
    verify_writes: bool = True,
    stop_on_close: bool = False,
):
    ...
```

Connection details belong to the `Connect Climate Chamber` keyword.

Importing the library must succeed even when:

- the chamber is powered off
- the network is disconnected
- the configured IP address is unavailable
- test discovery or `libdoc` is running

## 9. Required Keyword API

### 9.1 Connection and lifecycle

#### `Connect Climate Chamber`

Arguments:

- `ip: str`
- `temperature_min: float`
- `temperature_max: float`
- `port: int = 2049`
- `timeout: str | float = "1 second"`
- `response_timeout: str | float | None = None`
- `retries: int = 2`
- `retry_delay: str | float = "500 milliseconds"`
- `verify_writes: bool | None = None`
- `tcp_keepalive: bool = True`

Behavior:

- fail if an active driver session already exists unless `replace_existing=True`
- instantiate the driver with deferred or explicit connection
- connect and perform a harmless identification or status query
- log the chamber model, serial number, firmware/status information if available
- never log secrets; there are currently no credentials
- return the chamber identification string

#### `Disconnect Climate Chamber`

Arguments:

- `stop: bool | None = None`

Behavior:

- optionally stop the chamber before disconnecting
- use the library default when `stop` is not specified
- be idempotent
- do not fail when already disconnected unless strict mode is requested

#### `Reconnect Climate Chamber`

Reconnect and verify communication.

#### `Stop And Disconnect Climate Chamber`

Safety-oriented teardown keyword:

1. attempt to stop the chamber
2. always attempt to disconnect
3. preserve and report both errors if both operations fail
4. be suitable for `Suite Teardown`

#### `Climate Chamber Should Be Connected`

Perform a real communication check, not only a socket-object check.

#### `Get Climate Chamber Connection Statistics`

Return a Robot-compatible dictionary containing command, failure, and reconnect counters. Raw bytes must be converted to readable text or hexadecimal.

### 9.2 Identification and status

Required keywords:

- `Get Climate Chamber Identification`
- `Get Climate Chamber Serial Number`
- `Get Climate Chamber Model`
- `Get Climate Chamber Manufacturing Year`
- `Get Climate Chamber Status`
- `Get Climate Chamber Health`

`Get Climate Chamber Health` must return a dictionary suitable for Robot Framework variable assignment and logging.

### 9.3 Temperature control

Required keywords:

- `Set Climate Chamber Temperature`
- `Get Climate Chamber Setpoint`
- `Get Climate Chamber Temperature`
- `Set Climate Chamber Temperature Limits`
- `Get Climate Chamber Temperature Limits`
- `Start Climate Chamber`
- `Stop Climate Chamber`
- `Climate Chamber Should Be Running`
- `Climate Chamber Should Be Stopped`

`Set Climate Chamber Temperature` must use the driver safety limits and must never clamp an unsafe value silently.

### 9.4 Waiting and stabilization

Required keywords:

#### `Set Temperature And Wait`

Arguments:

- `target: float`
- `dwell: str | float = "0 seconds"`
- `tolerance: float = 0.8`
- `poll_interval: str | float = "10 seconds"`
- `timeout: str | float = "4 hours"`
- `stable_samples: int = 1`
- `start_chamber: bool = True`

Behavior:

- set the target
- optionally start the chamber
- wait for consecutive stable samples
- dwell after stability
- log periodic progress without flooding the Robot log
- return the final measured temperature
- fail with a clear timeout message containing target, last measurement, elapsed time, and stable sample count

#### `Wait Until Climate Chamber Is Stable`

Same stabilization behavior, but it must not change the setpoint and must not start the chamber unless explicitly requested.

#### `Wait For Climate Chamber Dwell`

Wait for a requested duration while periodically logging measured temperature.

Robot time values such as `500 ms`, `10 seconds`, `5 min`, and `2h` must be accepted.

### 9.5 Gradient control

Required keywords:

- `Set Climate Chamber Heating Gradient`
- `Get Climate Chamber Heating Gradient`
- `Set Climate Chamber Cooling Gradient`
- `Get Climate Chamber Cooling Gradient`

Use Celsius per minute in documentation and return values.

### 9.6 Auxiliary outputs

Required keywords:

- `Set Climate Chamber Dryer`
- `Get Climate Chamber Dryer`
- `Set Climate Chamber Compressed Air`
- `Get Climate Chamber Compressed Air`

Boolean arguments must accept Robot Framework boolean values reliably.

### 9.7 Assertions

Provide a small instrument-specific assertion layer:

- `Climate Chamber Temperature Should Be`
- `Climate Chamber Temperature Should Be Within`
- `Climate Chamber Setpoint Should Be`
- `Climate Chamber Should Be Running`
- `Climate Chamber Should Be Stopped`

Failure messages must contain expected value, actual value, tolerance, and units.

Do not duplicate generic Robot Framework assertions when no chamber-specific context is added.

### 9.8 Advanced/raw command access

Do not expose arbitrary low-level protocol commands in the initial public API.

A future `Execute Climate Chamber Command` keyword may be added only when:

- it is clearly marked advanced/unsafe
- it validates command names
- it is disabled or omitted from normal examples
- its documentation explains that normal safety abstractions can be bypassed

## 10. State and Error Handling

Every keyword requiring a connection must call a common internal guard and fail with:

```text
Climate chamber is not connected. Run 'Connect Climate Chamber' first.
```

Driver exceptions must remain distinct internally:

- communication error
- protocol error
- command error
- timeout error
- safety error

The adapter may add keyword context but must preserve the original exception as the cause.

Example failure:

```text
Set Climate Chamber Temperature failed for 85.0 °C:
setpoint verification failed; chamber reported 84.5 °C.
```

Do not convert all failures into generic `AssertionError`.

## 11. Robot Logging

Use `robot.api.logger` in the adapter.

Logging levels:

- INFO: connect/disconnect, setpoint changes, start/stop, stabilization milestones
- DEBUG: raw response details, retries, communication statistics
- WARN: reconnects, transient communication failures, optional teardown stop failure
- ERROR: final operation failure

Requirements:

- no `print()` calls from adapter keywords
- no ANSI terminal color sequences in Robot logs
- raw binary protocol data must be escaped or hexadecimal
- periodic wait logging must be rate-limited
- logs must include units

## 12. Time Conversion

Create one internal helper that accepts:

- numeric seconds
- Robot Framework time strings
- `None` where permitted

Use Robot Framework’s supported time conversion utilities or an equivalent well-tested converter.

Reject:

- negative timeout
- zero polling interval
- non-finite numbers
- malformed strings

## 13. Safety Requirements

1. Temperature minimum must be lower than maximum.
2. Setpoints outside configured limits must fail immediately.
3. The adapter must never silently clamp setpoints.
4. Teardown must make stop behavior explicit and configurable.
5. Disconnecting must not automatically stop the chamber unless configured or requested.
6. `Stop And Disconnect Climate Chamber` must always attempt disconnect even when stop fails.
7. Long waits must always have a finite default timeout.
8. Timeout messages must not leave the connection object in an undefined state.
9. Reconnect must not reapply or alter the chamber setpoint automatically.
10. Raw command access is out of MVP scope.
11. Hardware tests must have an emergency stop procedure documented.
12. CI tests must never require access to real hardware.

## 14. Unit Testing

Use pytest for Python unit tests.

Required unit test coverage:

- adapter imports without network access
- constructor has no hardware side effects
- connection keyword creates the driver with correct parameters
- repeated connect behavior
- idempotent disconnect
- stop-and-disconnect when stop passes
- stop-and-disconnect when stop fails
- stop-and-disconnect when disconnect also fails
- all connection guards
- float, integer, boolean, and Robot time conversion
- safety-limit failures
- keyword return types
- driver exception preservation
- Robot log integration
- no accidental keyword exposure
- all assertion success/failure paths
- long-wait timeout message
- stable sample counting
- progress log rate limiting

Use a fake driver object for adapter unit tests.

Minimum target:

- 90% line coverage for adapter code
- 85% branch coverage for adapter code
- driver regression coverage for every modified driver path

## 15. Protocol and Driver Tests

Create a deterministic fake TCP chamber server that can simulate:

- normal command response
- split response across multiple packets
- multiple bytes arriving after a terminator
- delayed response
- malformed status code
- `read failed`
- socket closure during command
- timeout
- retry followed by success
- response larger than configured maximum
- incorrect setpoint readback
- delayed running-state transition
- invalid digital output value

These tests must run without physical hardware.

## 16. Robot Framework Acceptance Tests

Create Robot Framework suites that exercise the adapter against the fake driver/server.

Required acceptance cases:

1. Import library and generate keyword documentation.
2. Connect and read identification.
3. Set and read temperature.
4. Start and stop chamber.
5. Wait for simulated stabilization.
6. Stabilization timeout.
7. Safety-limit rejection.
8. Dryer and compressed-air control.
9. Reconnect after simulated link failure.
10. Suite teardown after a failed test.
11. No internal Python helper methods visible as keywords.
12. Return dictionaries are usable from Robot syntax.

Run acceptance tests using:

```text
robot --outputdir results tests/robot
```

## 17. Real Hardware Verification

Real-hardware tests must be tagged:

```robot
[Tags]    hardware    climate_chamber
```

They must not run in normal CI.

Minimum hardware smoke test:

1. connect
2. read identification
3. read current temperature and setpoint
4. record current running state
5. set a safe, operator-approved setpoint
6. verify readback
7. start only when explicitly enabled by a command-line variable
8. wait for a short communication/stability interval
9. restore the original setpoint and running state when safe
10. disconnect
11. save Robot log, output XML, and communication diagnostics

Required command-line safety variable:

```text
--variable ALLOW_CHAMBER_CONTROL:False
```

Control-changing hardware tests must skip unless this variable is explicitly set to true.

## 18. Documentation

README must include:

- supported chamber/protocol statement
- architecture diagram showing Robot adapter over Python driver
- installation instructions
- first working Robot test
- suite setup and teardown example
- temperature stabilization example
- error handling examples
- real-hardware safety warning
- troubleshooting for connection refused, timeout, malformed response, and failed readback
- API compatibility statement
- supported Python and Robot Framework versions
- development and test commands

Generate keyword documentation:

```text
python -m robot.libdoc \
    votsch_climate_chamber.robot_library.VotschClimateChamberLibrary \
    docs/VotschClimateChamberLibrary.html
```

Libdoc generation must not connect to hardware.

## 19. Packaging

Distribution name:

```text
robotframework-votsch-climate-chamber
```

Python package:

```text
votsch_climate_chamber
```

Recommended dependencies:

```toml
dependencies = [
    "robotframework>=7.4,<8",
]
```

`colorama` should either be optional or removed from structured logging paths.

Provide a wheel and source distribution. Verify installation in a clean virtual environment.

## 20. CI Requirements

CI must run on Windows and Linux.

Required jobs:

- formatting/linting
- static type checking
- Python unit tests
- fake TCP protocol tests
- Robot acceptance tests
- package build
- clean-install smoke test
- `libdoc` generation
- artifact upload for Robot reports and generated keyword documentation

No CI job may require chamber hardware.

## 21. Implementation Gates

### Gate A — Driver review and architecture

Deliver:

- driver review report
- accepted driver changes
- adapter public keyword specification
- fake driver design
- package skeleton

Exit criteria:

- no unresolved high-severity driver issue
- no network access during library import
- keyword names approved
- safety defaults approved

### Gate B — Core adapter

Implement:

- connection lifecycle
- identification/status
- temperature read/set
- start/stop
- error translation
- Robot logging
- initial unit tests

Exit criteria:

- core unit tests pass
- adapter import and `libdoc` work offline
- no internal method exposure

### Gate C — Stabilization and auxiliary control

Implement:

- wait and dwell keywords
- timeout handling
- gradients
- dryer
- compressed air
- assertions
- fake protocol server

Exit criteria:

- Robot acceptance suite passes
- all simulated communication failures are covered
- no infinite wait path with default settings

### Gate D — Packaging and documentation

Implement:

- pyproject packaging
- examples
- README
- keyword documentation
- build/run scripts
- CI

Exit criteria:

- wheel installs in a clean environment
- examples parse and run against the simulator
- generated keyword documentation is complete

### Gate E — Hardware validation and release candidate

Perform:

- controlled real-hardware smoke test
- reconnect test
- long-running observation
- teardown interruption test
- release checklist

Exit criteria:

- hardware report attached
- original chamber state restored where safe
- no critical or high issue remains
- RC package and changelog produced

## 22. Acceptance Criteria

The task is complete when all of the following are true:

1. The original driver remains usable independently from Robot Framework.
2. Robot library import performs no network operation.
3. Only decorated, documented methods are visible as keywords.
4. The adapter uses composition rather than inheritance.
5. A suite-scoped connection can be opened, reused, stopped, and closed safely.
6. Unsafe temperatures fail before any command is sent.
7. Stabilization uses finite default timeouts and consecutive stable samples.
8. Robot time syntax is accepted.
9. Driver exceptions produce clear Robot failures without losing their type/cause.
10. `libdoc` is generated successfully without hardware.
11. Unit, fake-protocol, and Robot acceptance tests pass on Windows and Linux.
12. Real-hardware tests are opt-in and protected by an explicit control variable.
13. Package installation works from a built wheel.
14. Documentation includes safe setup and teardown examples.
15. No raw protocol keyword is exposed in the initial release.

## 23. Non-Goals for Initial Release

- humidity control unless the driver is extended with a defined safe API
- program/profile upload and execution
- multiple chamber sessions inside one library instance
- asynchronous background polling
- remote Robot Framework server mode
- arbitrary raw command execution
- GUI configuration
- automatic hardware discovery
- automatic restoration after host power loss

These can be planned after the core adapter is stable.

## 24. Final Recommendation

Use the supplied file as the stable Python driver foundation, perform a focused hardening review, and create a separate Robot Framework adapter.

Do not directly turn the existing `ClimateChamber` class into the Robot library. Direct conversion would mix protocol, instrument-domain, lifecycle, and Robot-specific responsibilities and would make both APIs harder to test and maintain.
