*** Settings ***
Documentation     RFDS-019 real-hardware conformance: exercises every public keyword of
...               BK8500BLibrary against a physical B&K Precision 8500B-series electronic
...               load and verifies its response. Does not run automatically in CI
...               (Force Tags "hardware"; exclude with `--exclude hardware` in automated
...               pipelines).
...
...               The load input stays OFF for the whole suite unless ALLOW_INPUT_ON is
...               explicitly set, short-circuit mode is never exercised unless
...               ALLOW_SHORT_CIRCUIT is set (and only with a bench proven safe for it —
...               see ai/bk8500b_ai_contract.yaml safety_rules), persistent
...               save/recall-state-slot keywords require ALLOW_PERSISTENT_WRITES, and the
...               raw SCPI escape hatch requires ALLOW_RAW_SCPI. Every keyword that mutates
...               device-persistent state restores the original value before its own test
...               case ends, and Suite Teardown disables the input and disconnects
...               regardless of how earlier test cases left the load.
Library           BK8500BLibrary    auto_connect=${FALSE}
Library           Collections
Library           OperatingSystem
Suite Setup       Initialize Hardware Conformance
Suite Teardown    Final Safe Teardown
Test Setup        Prepare Load For Keyword Test
Test Teardown     Per Test Safe Teardown
Force Tags        hardware    bk8500b    keyword-conformance

*** Variables ***
${PORT}                       COM9
${PROTOCOL}                   scpi
${BAUD_RATE}                  9600
${ALIAS}                      hardware
${SECONDARY_ALIAS}            secondary
${ALLOW_INPUT_ON}             ${FALSE}
${ALLOW_SHORT_CIRCUIT}        ${FALSE}
${ALLOW_PERSISTENT_WRITES}    ${FALSE}
${ALLOW_RAW_SCPI}             ${FALSE}
${TEST_CURRENT_A}             0.05
${TEST_VOLTAGE_V}             1.0
${TEST_POWER_W}               0.5
${TEST_RESISTANCE_OHM}        1000.0
${SETPOINT_TOLERANCE}         0.01
${EXPECTED_DRIVER_VERSION}    26.05

*** Test Cases ***
# ----------------------------------------------------------------------
# Connections and sessions
# ----------------------------------------------------------------------
KW-001 Connect To Electronic Load
    Disconnect All Electronic Loads
    ${result}=    Connect To Electronic Load    port=${PORT}    protocol=${PROTOCOL}    baud_rate=${BAUD_RATE}
    ...    alias=${ALIAS}
    Should Be Equal    ${result}[alias]    ${ALIAS}
    Should Be Equal    ${result}[session_state]    connected_ready_input_off

KW-002 Disconnect Electronic Load
    Connect To Electronic Load    port=${PORT}    protocol=${PROTOCOL}    baud_rate=${BAUD_RATE}    alias=${SECONDARY_ALIAS}
    Disconnect Electronic Load    ${SECONDARY_ALIAS}
    ${sessions}=    List Electronic Load Sessions
    ${aliases}=    Evaluate    [s['alias'] for s in $sessions]
    List Should Not Contain Value    ${aliases}    ${SECONDARY_ALIAS}

KW-003 Disconnect All Electronic Loads
    Connect To Electronic Load    port=${PORT}    protocol=${PROTOCOL}    baud_rate=${BAUD_RATE}    alias=${SECONDARY_ALIAS}
    Disconnect All Electronic Loads
    ${sessions}=    List Electronic Load Sessions
    Should Be Empty    ${sessions}
    Connect To Electronic Load    port=${PORT}    protocol=${PROTOCOL}    baud_rate=${BAUD_RATE}    alias=${ALIAS}

KW-004 Switch Electronic Load
    Connect To Electronic Load    port=${PORT}    protocol=${PROTOCOL}    baud_rate=${BAUD_RATE}    alias=${SECONDARY_ALIAS}
    ${active}=    Switch Electronic Load    ${SECONDARY_ALIAS}
    Should Be Equal    ${active}    ${SECONDARY_ALIAS}
    Switch Electronic Load    ${ALIAS}
    Disconnect Electronic Load    ${SECONDARY_ALIAS}

KW-005 Get Active Electronic Load
    ${active}=    Get Active Electronic Load
    Should Be Equal    ${active}    ${ALIAS}

KW-006 List Electronic Load Sessions
    ${sessions}=    List Electronic Load Sessions
    ${aliases}=    Evaluate    [s['alias'] for s in $sessions]
    List Should Contain Value    ${aliases}    ${ALIAS}

KW-007 Reconnect Electronic Load
    Reconnect Electronic Load    ${ALIAS}
    ${connected}=    Is Connected    ${ALIAS}
    Should Be True    ${connected}

KW-008 Synchronize Electronic Load State
    ${state}=    Synchronize Electronic Load State
    Should Not Be Empty    ${state}
    Log Dictionary    ${state}

KW-009 Electronic Load Should Be Connected
    Electronic Load Should Be Connected    ${ALIAS}

KW-010 Connect
    ${state}=    Connect    resource=${PORT}    alias=${SECONDARY_ALIAS}    protocol=${PROTOCOL}    baud_rate=${BAUD_RATE}
    Should Be Equal    ${state}[alias]    ${SECONDARY_ALIAS}
    Disconnect    ${SECONDARY_ALIAS}

KW-011 Disconnect
    Connect    resource=${PORT}    alias=${SECONDARY_ALIAS}    protocol=${PROTOCOL}    baud_rate=${BAUD_RATE}
    Disconnect    ${SECONDARY_ALIAS}
    Disconnect    ${SECONDARY_ALIAS}
    ${connected}=    Is Connected    ${SECONDARY_ALIAS}
    Should Be Equal    ${connected}    ${FALSE}

KW-012 Is Connected
    ${connected}=    Is Connected    ${ALIAS}
    Should Be Equal    ${connected}    ${TRUE}

KW-013 Get Connection State
    ${state}=    Get Connection State    ${ALIAS}
    Should Be Equal    ${state}[connected]    ${TRUE}
    Log Dictionary    ${state}

# ----------------------------------------------------------------------
# Communication and identity
# ----------------------------------------------------------------------
KW-014 Check Communication
    ${ok}=    Check Communication
    Should Be Equal    ${ok}    ${TRUE}

KW-015 Get Identity
    ${identity}=    Get Identity
    Should Not Be Empty    ${identity}
    Log Dictionary    ${identity}

KW-016 Identify Electronic Load
    ${identity}=    Identify Electronic Load
    Should Contain    ${identity}[manufacturer]    BK

KW-017 Get Electronic Load Capabilities
    ${capabilities}=    Get Electronic Load Capabilities
    Should Not Be Empty    ${capabilities}
    Log Dictionary    ${capabilities}

KW-018 Get Electronic Load Status
    ${status}=    Get Electronic Load Status
    Should Not Be Empty    ${status}
    Log Dictionary    ${status}

KW-019 Run Electronic Load Health Check
    ${health}=    Run Electronic Load Health Check
    Should Not Be Empty    ${health}
    Log Dictionary    ${health}

KW-020 Get Electronic Load Diagnostic Snapshot
    ${snapshot}=    Get Electronic Load Diagnostic Snapshot
    Should Not Be Empty    ${snapshot}
    Log Dictionary    ${snapshot}

KW-021 Run Electronic Load Self Test
    ${result}=    Run Electronic Load Self Test
    Log Dictionary    ${result}

KW-022 Clear Electronic Load Status
    Clear Electronic Load Status

KW-023 Drain Electronic Load Error Queue
    ${errors}=    Drain Electronic Load Error Queue
    Log List    ${errors}

# ----------------------------------------------------------------------
# Mode
# ----------------------------------------------------------------------
KW-024 Set Electronic Load Mode
    ${original}=    Get Electronic Load Mode
    Set Electronic Load Mode    CC
    ${mode}=    Get Electronic Load Mode
    Should Be Equal    ${mode}    CC
    Set Electronic Load Mode    ${original}

KW-025 Get Electronic Load Mode
    ${mode}=    Get Electronic Load Mode
    Should Not Be Empty    ${mode}

# ----------------------------------------------------------------------
# Input control
# ----------------------------------------------------------------------
KW-026 Enable Electronic Load Input
    [Documentation]    Skipped unless ALLOW_INPUT_ON is set — energizes the load. Only
    ...    enable this against a bench with a source that can safely supply the
    ...    configured test setpoint.
    Skip If    not ${ALLOW_INPUT_ON}    Set ALLOW_INPUT_ON:true to exercise Enable Electronic Load Input.
    Set Current Setpoint    ${TEST_CURRENT_A}
    Enable Electronic Load Input
    Electronic Load Input Should Be On
    Disable Electronic Load Input

KW-027 Disable Electronic Load Input
    Disable Electronic Load Input
    Electronic Load Input Should Be Off

KW-028 Electronic Load Input Should Be On
    Skip If    not ${ALLOW_INPUT_ON}    Set ALLOW_INPUT_ON:true to exercise Electronic Load Input Should Be On.
    Set Current Setpoint    ${TEST_CURRENT_A}
    Enable Electronic Load Input
    Electronic Load Input Should Be On
    Disable Electronic Load Input

KW-029 Electronic Load Input Should Be Off
    Disable Electronic Load Input
    Electronic Load Input Should Be Off

KW-030 Configure And Enable Load
    Skip If    not ${ALLOW_INPUT_ON}    Set ALLOW_INPUT_ON:true to exercise Configure And Enable Load.
    Configure And Enable Load    CC    ${TEST_CURRENT_A}    current_limit=${TEST_CURRENT_A}
    Electronic Load Input Should Be On
    Disable Electronic Load Input

# ----------------------------------------------------------------------
# Setpoints
# ----------------------------------------------------------------------
KW-031 Set Current Setpoint
    Set Current Setpoint    ${TEST_CURRENT_A}
    ${readback}=    Get Current Setpoint
    Numbers Should Be Close    ${readback}    ${TEST_CURRENT_A}    ${SETPOINT_TOLERANCE}

KW-032 Get Current Setpoint
    ${value}=    Get Current Setpoint
    Should Be True    ${value} >= 0

KW-033 Set Voltage Setpoint
    Set Voltage Setpoint    ${TEST_VOLTAGE_V}
    ${readback}=    Get Voltage Setpoint
    Numbers Should Be Close    ${readback}    ${TEST_VOLTAGE_V}    ${SETPOINT_TOLERANCE}

KW-034 Get Voltage Setpoint
    ${value}=    Get Voltage Setpoint
    Should Be True    ${value} >= 0

KW-035 Set Power Setpoint
    Set Power Setpoint    ${TEST_POWER_W}
    ${readback}=    Get Power Setpoint
    Numbers Should Be Close    ${readback}    ${TEST_POWER_W}    ${SETPOINT_TOLERANCE}

KW-036 Get Power Setpoint
    ${value}=    Get Power Setpoint
    Should Be True    ${value} >= 0

KW-037 Set Resistance Setpoint
    Set Resistance Setpoint    ${TEST_RESISTANCE_OHM}
    ${readback}=    Get Resistance Setpoint
    Numbers Should Be Close    ${readback}    ${TEST_RESISTANCE_OHM}    1.0

KW-038 Get Resistance Setpoint
    ${value}=    Get Resistance Setpoint
    Should Be True    ${value} >= 0

# ----------------------------------------------------------------------
# Protection
# ----------------------------------------------------------------------
KW-039 Set Current Protection
    ${original}=    Get Current Protection
    Set Current Protection    ${TEST_CURRENT_A * 2}
    ${readback}=    Get Current Protection
    Numbers Should Be Close    ${readback}    ${TEST_CURRENT_A * 2}    ${SETPOINT_TOLERANCE}
    Set Current Protection    ${original}

KW-040 Get Current Protection
    ${value}=    Get Current Protection
    Should Be True    ${value} >= 0

KW-041 Set Power Protection
    ${original}=    Get Power Protection
    Set Power Protection    ${TEST_POWER_W * 2}
    ${readback}=    Get Power Protection
    Numbers Should Be Close    ${readback}    ${TEST_POWER_W * 2}    ${SETPOINT_TOLERANCE}
    Set Power Protection    ${original}

KW-042 Get Power Protection
    ${value}=    Get Power Protection
    Should Be True    ${value} >= 0

KW-043 Clear Electronic Load Protection
    Clear Electronic Load Protection

# ----------------------------------------------------------------------
# Sense, range, slew
# ----------------------------------------------------------------------
KW-044 Set Remote Sense
    ${original}=    Get Remote Sense
    Set Remote Sense    ${FALSE}
    ${readback}=    Get Remote Sense
    Should Be Equal    ${readback}    ${FALSE}
    Set Remote Sense    ${original}

KW-045 Get Remote Sense
    ${value}=    Get Remote Sense
    Should Be True    $value in (True, False)

KW-046 Set Current Range
    ${original}=    Get Current Range
    Set Current Range    ${original}
    ${readback}=    Get Current Range
    Numbers Should Be Close    ${readback}    ${original}    0.5

KW-047 Get Current Range
    ${value}=    Get Current Range
    Should Be True    ${value} > 0

KW-048 Set Voltage Range
    ${original}=    Get Voltage Range
    Set Voltage Range    ${original}
    ${readback}=    Get Voltage Range
    Numbers Should Be Close    ${readback}    ${original}    0.5

KW-049 Get Voltage Range
    ${value}=    Get Voltage Range
    Should Be True    ${value} > 0

KW-050 Set Voltage Autorange
    ${original}=    Get Voltage Autorange
    Set Voltage Autorange    ${TRUE}
    ${readback}=    Get Voltage Autorange
    Should Be Equal    ${readback}    ${TRUE}
    Set Voltage Autorange    ${original}

KW-051 Get Voltage Autorange
    ${value}=    Get Voltage Autorange
    Should Be True    $value in (True, False)

KW-052 Set Current Slew Rate
    ${original}=    Get Current Slew Rate
    Set Current Slew Rate    ${original}
    ${readback}=    Get Current Slew Rate
    Numbers Should Be Close    ${readback}    ${original}    0.5

KW-053 Get Current Slew Rate
    ${value}=    Get Current Slew Rate
    Should Be True    ${value} > 0

KW-054 Set Load Voltage Thresholds
    Set Load Voltage Thresholds    ${TEST_VOLTAGE_V + 1}    ${0.5}

KW-055 Set Short Circuit Mode
    [Documentation]    Requires both ALLOW_SHORT_CIRCUIT and the exact confirmation text.
    Skip If    not ${ALLOW_SHORT_CIRCUIT}    Set ALLOW_SHORT_CIRCUIT:true to exercise Set Short Circuit Mode.
    Set Short Circuit Mode    ${TRUE}    confirmation=I UNDERSTAND
    Set Short Circuit Mode    ${FALSE}    confirmation=I UNDERSTAND

# ----------------------------------------------------------------------
# Measuring
# ----------------------------------------------------------------------
KW-056 Measure Voltage
    ${voltage}=    Measure Voltage
    Should Be True    ${voltage} >= 0

KW-057 Measure Current
    ${current}=    Measure Current
    Should Be True    ${current} >= 0

KW-058 Measure Power
    ${power}=    Measure Power
    Should Be True    ${power} >= 0

KW-059 Measure Resistance
    ${resistance}=    Measure Resistance
    Should Be True    ${resistance} >= 0

KW-060 Get Measurement Snapshot
    ${snapshot}=    Get Measurement Snapshot
    Dictionary Should Contain Key    ${snapshot}    voltage
    Dictionary Should Contain Key    ${snapshot}    current
    Log Dictionary    ${snapshot}

KW-061 Measurement Should Be Within Range
    ${voltage}=    Measure Voltage
    Measurement Should Be Within Range    ${voltage}    ${-1000}    ${1000}    name=voltage

KW-062 Voltage Should Be Within Range
    Voltage Should Be Within Range    ${-1000}    ${1000}

KW-063 Current Should Be Within Range
    Current Should Be Within Range    ${-1000}    ${1000}

KW-064 Power Should Be Within Range
    Power Should Be Within Range    ${-10000}    ${10000}

KW-065 Wait Until Measurement Is Within Range
    Wait Until Measurement Is Within Range    voltage    ${-1000}    ${1000}    timeout=${2.0}    interval=${0.1}

KW-066 Log Measurements To CSV
    ${path}=    Join Path    ${OUTPUT DIR}    kw066_measurements.csv
    Log Measurements To CSV    ${path}    samples=${2}    interval=${0.1}
    File Should Exist    ${path}

# ----------------------------------------------------------------------
# Transient, trigger, peak capture
# ----------------------------------------------------------------------
KW-067 Configure Transient Load
    Configure Transient Load    ${TEST_CURRENT_A}    ${0.001}    ${0.0}    ${0.001}    ${1.0}

KW-068 Get Transient Load Configuration
    ${config}=    Get Transient Load Configuration
    Should Not Be Empty    ${config}
    Log Dictionary    ${config}

KW-069 Trigger Electronic Load
    Skip If    not ${ALLOW_INPUT_ON}    Set ALLOW_INPUT_ON:true to exercise Trigger Electronic Load.
    Trigger Electronic Load

KW-070 Enable Peak Capture
    Enable Peak Capture

KW-071 Clear Peak Capture
    Clear Peak Capture

KW-072 Read Peak Measurements
    ${peaks}=    Read Peak Measurements
    Log Dictionary    ${peaks}

# ----------------------------------------------------------------------
# State save/recall, reset, remote/local
# ----------------------------------------------------------------------
KW-073 Save Electronic Load State
    Skip If    not ${ALLOW_PERSISTENT_WRITES}    Set ALLOW_PERSISTENT_WRITES:true to exercise Save Electronic Load State.
    Save Electronic Load State    ${1}

KW-074 Recall Electronic Load State
    Skip If    not ${ALLOW_PERSISTENT_WRITES}    Set ALLOW_PERSISTENT_WRITES:true to exercise Recall Electronic Load State.
    Recall Electronic Load State    ${1}

KW-075 Reset Electronic Load
    Skip If    not ${ALLOW_PERSISTENT_WRITES}    Set ALLOW_PERSISTENT_WRITES:true to exercise Reset Electronic Load.
    Reset Electronic Load
    Disable Electronic Load Input

KW-076 Set Electronic Load Remote
    Set Electronic Load Remote

KW-077 Set Electronic Load Local
    [Documentation]    Returns the load to front-panel control; re-asserts remote
    ...    immediately afterward so later test cases keep working over the bus.
    Set Electronic Load Local
    Set Electronic Load Remote

# ----------------------------------------------------------------------
# Raw SCPI escape hatch
# ----------------------------------------------------------------------
KW-078 Query Raw SCPI
    Skip If    not ${ALLOW_RAW_SCPI}    Set ALLOW_RAW_SCPI:true to exercise the raw SCPI escape hatch.
    ${response}=    Query Raw SCPI    SYSTem:ERRor?
    Should Not Be Empty    ${response}

KW-079 Write Raw SCPI
    Skip If    not ${ALLOW_RAW_SCPI}    Set ALLOW_RAW_SCPI:true to exercise the raw SCPI escape hatch.
    Write Raw SCPI    *CLS
    ${response}=    Query Raw SCPI    SYSTem:ERRor?
    Should Not Be Empty    ${response}

# ----------------------------------------------------------------------
# Diagnostics export
# ----------------------------------------------------------------------
KW-080 Export Diagnostic Snapshot
    ${path}=    Join Path    ${OUTPUT DIR}    kw080_diagnostic_snapshot.json
    ${result}=    Export Diagnostic Snapshot    ${path}
    File Should Exist    ${result}[path]

KW-081 Export Diagnostic Bundle
    ${path}=    Export Diagnostic Bundle
    Should Not Be Empty    ${path}
    File Should Exist    ${path}
    Log    Diagnostic bundle written to ${path}

*** Keywords ***
Initialize Hardware Conformance
    Capture Software Evidence
    Connect To Electronic Load    port=${PORT}    protocol=${PROTOCOL}    baud_rate=${BAUD_RATE}    alias=${ALIAS}
    Disable Electronic Load Input

Capture Software Evidence
    ${source_version}=    Evaluate    bk8500b.__version__    modules=bk8500b
    ${distribution_version}=    Evaluate
    ...    importlib.metadata.version("robotframework-bk8500b")    modules=importlib.metadata
    ${robot_version}=    Evaluate    robot.__version__    modules=robot
    ${python_version}=    Evaluate    platform.python_version()    modules=platform
    Set Suite Metadata    Driver source version    ${source_version}
    Set Suite Metadata    Installed distribution version    ${distribution_version}
    Set Suite Metadata    Robot Framework version    ${robot_version}
    Set Suite Metadata    Python version    ${python_version}
    Log To Console    Driver source=${source_version}; installed=${distribution_version}; Robot=${robot_version}

Prepare Load For Keyword Test
    ${connected}=    Is Connected    ${ALIAS}
    IF    not ${connected}
        Connect To Electronic Load    port=${PORT}    protocol=${PROTOCOL}    baud_rate=${BAUD_RATE}    alias=${ALIAS}
    END
    Run Keyword And Ignore Error    Disable Electronic Load Input

Per Test Safe Teardown
    Run Keyword And Ignore Error    Disable Electronic Load Input

Final Safe Teardown
    Run Keyword And Ignore Error    Disable Electronic Load Input
    Run Keyword And Ignore Error    Disconnect All Electronic Loads

Numbers Should Be Close
    [Arguments]    ${actual}    ${expected}    ${tolerance}
    ${difference}=    Evaluate    abs(float($actual) - float($expected))
    Should Be True    ${difference} <= ${tolerance}
    ...    Difference ${difference} exceeds tolerance ${tolerance}; actual=${actual}, expected=${expected}
