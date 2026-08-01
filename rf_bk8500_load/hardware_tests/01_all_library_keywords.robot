*** Settings ***
Documentation     Full real-device conformance test for every public BK8500Library keyword.
...               The suite communicates with the physical load, verifies command replies and
...               readback where available, and reports each keyword independently.
...               The input remains OFF unless ALLOW_INPUT_ON is explicitly true.
...               Persistent list/settings slots are untouched unless ALLOW_PERSISTENT_WRITES is true.
Library           BK8500Library    auto_connect=${FALSE}
Library           Collections
Suite Setup       Initialize Hardware Conformance
Suite Teardown    Final Safe Teardown
Test Setup        Prepare Hardware For Keyword Test
Test Teardown     Per Test Safe Teardown

*** Variables ***
${PORT}                         COM9
${BAUDRATE}                     9600
${MODEL}                        8500
${ADDRESS}                      0
${TIMEOUT}                      1.0
${AUTO_DETECT_BAUDRATE}          ${FALSE}
${BAUDRATE_CANDIDATES}           4800,9600,19200,38400
${PROBE_TIMEOUT}                 0.75
${HARDWARE_ALIAS}               hardware
${SECONDARY_ALIAS}              secondary
${TEST_CURRENT_A}               0.05
${TEST_VOLTAGE_V}               1.0
${TEST_POWER_W}                 0.5
${TEST_RESISTANCE_OHM}          1000.0
${TEST_BATTERY_CUTOFF_V}        0.5
${TEST_TIMER_S}                 2
${SETPOINT_TOLERANCE}           0.002
${VOLTAGE_TOLERANCE}            0.5
${CURRENT_TOLERANCE}            0.05
${POWER_TOLERANCE}              0.5
${SETTINGS_REGISTER}            25
${LIST_FILE_SLOT}               8
${ALLOW_INPUT_ON}               ${FALSE}
${ALLOW_PERSISTENT_WRITES}      ${FALSE}
${EXPECTED_DRIVER_VERSION}       26.16.0

*** Test Cases ***
KW-001 Open Load Connection
    [Documentation]    Reopen the real serial connection and verify alias and transport data.
    Close Load Connection    ${HARDWARE_ALIAS}
    ${alias}=    Open Load Connection    port=${PORT}    baudrate=${BAUDRATE}
    ...    model=${MODEL}    alias=${HARDWARE_ALIAS}    address=${ADDRESS}
    ...    timeout=${TIMEOUT}    simulated=${FALSE}    identify=${TRUE}
    ...    auto_detect_baudrate=${AUTO_DETECT_BAUDRATE}
    ...    baudrate_candidates=${BAUDRATE_CANDIDATES}    probe_timeout=${PROBE_TIMEOUT}
    Should Be Equal    ${alias}    ${HARDWARE_ALIAS}
    ${info}=    Get Load Connection Info
    Should Be Equal    ${info}[alias]    ${HARDWARE_ALIAS}
    Should Contain    ${info}[transport]    ${PORT}

KW-002 Switch Load Connection
    [Documentation]    Switch between a real connection and a secondary simulated connection.
    Open Load Connection    simulated=${TRUE}    model=${MODEL}    alias=${SECONDARY_ALIAS}
    ${previous}=    Switch Load Connection    ${HARDWARE_ALIAS}
    Should Be Equal    ${previous}    ${SECONDARY_ALIAS}
    ${previous}=    Switch Load Connection    ${SECONDARY_ALIAS}
    Should Be Equal    ${previous}    ${HARDWARE_ALIAS}
    ${info}=    Get Load Connection Info
    Should Be Equal    ${info}[alias]    ${SECONDARY_ALIAS}
    Switch Load Connection    ${HARDWARE_ALIAS}
    Close Load Connection    ${SECONDARY_ALIAS}

KW-003 Close Load Connection
    [Documentation]    Close one selected connection and prove that its alias is no longer selectable.
    Open Load Connection    simulated=${TRUE}    model=${MODEL}    alias=${SECONDARY_ALIAS}
    Close Load Connection    ${SECONDARY_ALIAS}
    Run Keyword And Expect Error    *Unknown load alias*    Switch Load Connection    ${SECONDARY_ALIAS}
    Switch Load Connection    ${HARDWARE_ALIAS}

KW-005 Get Load Product Information
    ${identity}=    Get Load Product Information
    Dictionary Should Contain Key    ${identity}    model
    Dictionary Should Contain Key    ${identity}    serial_number
    Dictionary Should Contain Key    ${identity}    firmware_version
    Should Not Be Empty    ${identity}[model]
    Log Dictionary    ${identity}

KW-006 Get Load Rated Limits
    ${limits}=    Get Load Rated Limits
    Should Be True    ${limits}[max_voltage_v] > 0
    Should Be True    ${limits}[max_current_a] > 0
    Should Be True    ${limits}[max_power_w] > 0
    Log Dictionary    ${limits}

KW-007 Claim Remote Control
    Claim Remote Control
    ${reading}=    Measure Load Input
    Should Be Equal    ${reading}[operation_state][remote_control_enabled]    ${TRUE}

KW-008 Release Remote Control
    Release Remote Control
    ${reading}=    Measure Load Input
    Should Be Equal    ${reading}[operation_state][remote_control_enabled]    ${FALSE}
    Claim Remote Control

KW-009 Set Local Key Enabled
    Set Local Key Enabled    ${FALSE}
    ${reading}=    Measure Load Input
    Should Be Equal    ${reading}[operation_state][local_key_enabled]    ${FALSE}
    Set Local Key Enabled    ${TRUE}
    ${reading}=    Measure Load Input
    Should Be Equal    ${reading}[operation_state][local_key_enabled]    ${TRUE}

KW-010 Load Input On
    Skip If    not ${ALLOW_INPUT_ON}    Set ALLOW_INPUT_ON:true to exercise the energized input command.
    Apply Constant Current    ${TEST_CURRENT_A}    enable_input=${FALSE}
    Load Input On
    Load Input State Should Be    ON
    Load Input Off

KW-011 Load Input Off
    Load Input Off
    Load Input State Should Be    OFF

KW-012 Reset Load To Safe State
    Reset Load To Safe State
    ${reading}=    Measure Load Input
    Should Be Equal    ${reading}[input_on]    ${FALSE}
    Should Be Equal    ${reading}[operation_state][remote_control_enabled]    ${FALSE}
    ${function}=    Get Load Function
    Should Be Equal    ${function}    FIXED

KW-013 Set Remote Sense
    Set Remote Sense    ${TRUE}
    ${enabled}=    Get Remote Sense
    Should Be Equal    ${enabled}    ${TRUE}
    Set Remote Sense    ${FALSE}
    ${enabled}=    Get Remote Sense
    Should Be Equal    ${enabled}    ${FALSE}

KW-014 Get Remote Sense
    ${enabled}=    Get Remote Sense
    Should Be True    $enabled is True or $enabled is False

KW-015 Configure Load Protection
    ${limits}=    Get Load Rated Limits
    Configure Load Protection    max_voltage=${limits}[max_voltage_v]
    ...    max_current=${limits}[max_current_a]    max_power=${limits}[max_power_w]
    ${readback}=    Get Load Protection Limits
    Numbers Should Be Close    ${readback}[max_voltage_v]    ${limits}[max_voltage_v]    0.01
    Numbers Should Be Close    ${readback}[max_current_a]    ${limits}[max_current_a]    0.001
    Numbers Should Be Close    ${readback}[max_power_w]    ${limits}[max_power_w]    0.01

KW-016 Get Load Protection Limits
    ${protection}=    Get Load Protection Limits
    Should Be True    ${protection}[max_voltage_v] >= 0
    Should Be True    ${protection}[max_current_a] >= 0
    Should Be True    ${protection}[max_power_w] >= 0
    Log Dictionary    ${protection}

KW-017 Set Load Mode
    ${result}=    Set Load Mode    CC
    Should Be Equal    ${result}    CC
    ${mode}=    Get Load Mode
    Should Be Equal    ${mode}    CC

KW-018 Get Load Mode
    Set Load Mode    CV
    ${mode}=    Get Load Mode
    Should Be Equal    ${mode}    CV

KW-019 Set Load Setpoint
    Set Load Setpoint    CC    ${TEST_CURRENT_A}
    ${readback}=    Get Load Setpoint    CC
    Numbers Should Be Close    ${readback}    ${TEST_CURRENT_A}    ${SETPOINT_TOLERANCE}

KW-020 Get Load Setpoint
    Set Load Setpoint    CV    ${TEST_VOLTAGE_V}
    ${readback}=    Get Load Setpoint    CV
    Numbers Should Be Close    ${readback}    ${TEST_VOLTAGE_V}    ${SETPOINT_TOLERANCE}

KW-021 Apply Constant Current
    Apply Constant Current    ${TEST_CURRENT_A}    enable_input=${FALSE}
    Load Mode Should Be    CC
    ${readback}=    Get Load Setpoint    CC
    Numbers Should Be Close    ${readback}    ${TEST_CURRENT_A}    ${SETPOINT_TOLERANCE}
    Load Input State Should Be    OFF

KW-022 Apply Constant Voltage
    Apply Constant Voltage    ${TEST_VOLTAGE_V}    enable_input=${FALSE}
    Load Mode Should Be    CV
    ${readback}=    Get Load Setpoint    CV
    Numbers Should Be Close    ${readback}    ${TEST_VOLTAGE_V}    ${SETPOINT_TOLERANCE}
    Load Input State Should Be    OFF

KW-023 Apply Constant Power
    Apply Constant Power    ${TEST_POWER_W}    enable_input=${FALSE}
    Load Mode Should Be    CW
    ${readback}=    Get Load Setpoint    CW
    Numbers Should Be Close    ${readback}    ${TEST_POWER_W}    ${SETPOINT_TOLERANCE}
    Load Input State Should Be    OFF

KW-024 Apply Constant Resistance
    Apply Constant Resistance    ${TEST_RESISTANCE_OHM}    enable_input=${FALSE}
    Load Mode Should Be    CR
    ${readback}=    Get Load Setpoint    CR
    Numbers Should Be Close    ${readback}    ${TEST_RESISTANCE_OHM}    0.1
    Load Input State Should Be    OFF

KW-025 Set Load Function
    ${result}=    Set Load Function    FIXED
    Should Be Equal    ${result}    FIXED
    ${readback}=    Get Load Function
    Should Be Equal    ${readback}    FIXED

KW-026 Set Load Function Unchecked
    [Documentation]    Exercises the unchecked path with FIXED; it intentionally does not select dangerous SHORT.
    ${result}=    Set Load Function Unchecked    FIXED
    Should Be Equal    ${result}    FIXED
    ${readback}=    Get Load Function
    Should Be Equal    ${readback}    FIXED

KW-027 Get Load Function
    Set Load Function    TRANSIENT
    ${function}=    Get Load Function
    Should Be Equal    ${function}    TRANSIENT
    Set Load Function    FIXED

KW-028 Configure Load Transient
    Configure Load Transient    CC    0.02    0.1    ${TEST_CURRENT_A}    0.2    CONTINUOUS
    ${transient}=    Get Load Transient    CC
    Should Be Equal    ${transient}[mode]    CC
    Numbers Should Be Close    ${transient}[level_a]    0.02    ${SETPOINT_TOLERANCE}
    Numbers Should Be Close    ${transient}[level_b]    ${TEST_CURRENT_A}    ${SETPOINT_TOLERANCE}
    Numbers Should Be Close    ${transient}[dwell_a_s]    0.1    0.001
    Numbers Should Be Close    ${transient}[dwell_b_s]    0.2    0.001
    Should Be Equal    ${transient}[operation]    CONTINUOUS

KW-029 Get Load Transient
    Configure Load Transient    CV    0.5    0.1    ${TEST_VOLTAGE_V}    0.2    PULSE
    ${transient}=    Get Load Transient    CV
    Should Be Equal    ${transient}[mode]    CV
    Should Be Equal    ${transient}[operation]    PULSE

KW-030 Set Load Trigger Source
    ${source}=    Set Load Trigger Source    BUS
    Should Be Equal    ${source}    BUS
    ${readback}=    Get Load Trigger Source
    Should Be Equal    ${readback}    BUS

KW-031 Get Load Trigger Source
    Set Load Trigger Source    IMMEDIATE
    ${source}=    Get Load Trigger Source
    Should Be Equal    ${source}    IMMEDIATE

KW-032 Trigger Load
    Set Load Trigger Source    BUS
    Trigger Load
    Set Load Trigger Source    IMMEDIATE

KW-033 Configure Load List
    ${steps}=    Evaluate    [(0.02, 0.1), (float($TEST_CURRENT_A), 0.2)]
    Configure Load List    CC    ${steps}    repeat=ONCE    name=RFTEST
    ${count}=    Get Load List Step Count
    Should Be Equal As Integers    ${count}    2
    ${step}=    Get Load List Step    CC    2
    Numbers Should Be Close    ${step}[level]    ${TEST_CURRENT_A}    ${SETPOINT_TOLERANCE}
    Numbers Should Be Close    ${step}[dwell_s]    0.2    0.001

KW-034 Get Load List Step
    ${steps}=    Evaluate    [(0.01, 0.1), (0.03, 0.2)]
    Configure Load List    CC    ${steps}    repeat=ONCE    name=RFSTEP
    ${step}=    Get Load List Step    CC    1
    Should Be Equal As Integers    ${step}[index]    1
    Numbers Should Be Close    ${step}[level]    0.01    ${SETPOINT_TOLERANCE}
    Numbers Should Be Close    ${step}[dwell_s]    0.1    0.001

KW-035 Get Load List Step Count
    ${steps}=    Evaluate    [(0.01, 0.1), (0.02, 0.1), (0.03, 0.1)]
    Configure Load List    CC    ${steps}
    ${count}=    Get Load List Step Count
    Should Be Equal As Integers    ${count}    3

KW-036 Save Load List File
    Skip If    not ${ALLOW_PERSISTENT_WRITES}    Set ALLOW_PERSISTENT_WRITES:true; this overwrites LIST_FILE_SLOT.
    ${steps}=    Evaluate    [(0.01, 0.1), (0.02, 0.2)]
    Configure Load List    CC    ${steps}    name=RFSAVE
    Save Load List File    ${LIST_FILE_SLOT}

KW-037 Recall Load List File
    [Documentation]    Verify that the recall command is accepted and that the saved profile is readable afterward.
    Skip If    not ${ALLOW_PERSISTENT_WRITES}    Set ALLOW_PERSISTENT_WRITES:true; this overwrites LIST_FILE_SLOT.
    ${saved}=    Evaluate    [(0.01, 0.1), (0.04, 0.2)]
    Configure Load List    CC    ${saved}    name=RFRECALL
    Save Load List File    ${LIST_FILE_SLOT}
    Recall Load List File    ${LIST_FILE_SLOT}
    ${count}=    Get Load List Step Count
    Should Be Equal As Integers    ${count}    2
    ${step}=    Get Load List Step    CC    2
    Numbers Should Be Close    ${step}[level]    0.04    ${SETPOINT_TOLERANCE}
    Numbers Should Be Close    ${step}[dwell_s]    0.2    0.001

WF-001 Save Reconfigure And Recall List
    [Documentation]    Regression for the COM9 result: save a valid two-step profile, edit another valid two-step profile, then recall and verify the original.
    Skip If    not ${ALLOW_PERSISTENT_WRITES}    Set ALLOW_PERSISTENT_WRITES:true; this overwrites LIST_FILE_SLOT.
    ${saved}=    Evaluate    [(0.01, 0.1), (0.04, 0.2)]
    Configure Load List    CC    ${saved}    name=RFSAVED
    Save Load List File    ${LIST_FILE_SLOT}
    ${replacement}=    Evaluate    [(0.02, 0.1), (0.03, 0.1)]
    Configure Load List    CC    ${replacement}    name=RFCHANGED
    ${replacement_count}=    Get Load List Step Count
    Should Be Equal As Integers    ${replacement_count}    2
    Recall Load List File    ${LIST_FILE_SLOT}
    ${restored_count}=    Get Load List Step Count
    Should Be Equal As Integers    ${restored_count}    2
    ${restored}=    Get Load List Step    CC    2
    Numbers Should Be Close    ${restored}[level]    0.04    ${SETPOINT_TOLERANCE}
    Numbers Should Be Close    ${restored}[dwell_s]    0.2    0.001

KW-038 Set Battery Cutoff Voltage
    Set Battery Cutoff Voltage    ${TEST_BATTERY_CUTOFF_V}
    ${readback}=    Get Battery Cutoff Voltage
    Numbers Should Be Close    ${readback}    ${TEST_BATTERY_CUTOFF_V}    0.001

KW-039 Get Battery Cutoff Voltage
    ${value}=    Get Battery Cutoff Voltage
    Should Be True    ${value} >= 0

KW-040 Set Load On Timer
    Set Load On Timer    ${TEST_TIMER_S}    enabled=${TRUE}
    ${timer}=    Get Load On Timer
    Should Be Equal As Numbers    ${timer}[seconds]    ${TEST_TIMER_S}
    Should Be Equal    ${timer}[enabled]    ${TRUE}
    Set Load On Timer    ${TEST_TIMER_S}    enabled=${FALSE}

KW-041 Get Load On Timer
    ${timer}=    Get Load On Timer
    Dictionary Should Contain Key    ${timer}    seconds
    Dictionary Should Contain Key    ${timer}    enabled

KW-042 Save Load Settings
    Skip If    not ${ALLOW_PERSISTENT_WRITES}    Set ALLOW_PERSISTENT_WRITES:true; this overwrites SETTINGS_REGISTER.
    Set Load Mode    CC
    Set Load Setpoint    CC    0.011
    Save Load Settings    ${SETTINGS_REGISTER}

KW-043 Recall Load Settings
    Skip If    not ${ALLOW_PERSISTENT_WRITES}    Set ALLOW_PERSISTENT_WRITES:true; this overwrites SETTINGS_REGISTER.
    Set Load Mode    CC
    Set Load Setpoint    CC    0.011
    Save Load Settings    ${SETTINGS_REGISTER}
    Set Load Setpoint    CC    0.033
    Recall Load Settings    ${SETTINGS_REGISTER}
    Claim Remote Control
    ${readback}=    Get Load Setpoint    CC
    Numbers Should Be Close    ${readback}    0.011    ${SETPOINT_TOLERANCE}

KW-044 Measure Load Input
    ${reading}=    Measure Load Input
    Dictionary Should Contain Key    ${reading}    voltage_v
    Dictionary Should Contain Key    ${reading}    current_a
    Dictionary Should Contain Key    ${reading}    power_w
    Dictionary Should Contain Key    ${reading}    input_on
    Log Dictionary    ${reading}

KW-045 Get Load Voltage
    ${voltage}=    Get Load Voltage
    Should Be True    ${voltage} >= 0

KW-046 Get Load Current
    ${current}=    Get Load Current
    Should Be True    ${current} >= 0

KW-047 Get Load Power
    ${power}=    Get Load Power
    Should Be True    ${power} >= 0

KW-048 Wait Until Load Reading Is Stable
    Load Input Off
    ${reading}=    Wait Until Load Reading Is Stable    quantity=current
    ...    tolerance=0.05    window=0.3    timeout=5.0    interval=0.1
    Dictionary Should Contain Key    ${reading}    current_a

KW-049 Load Voltage Should Be Within
    ${voltage}=    Get Load Voltage
    Load Voltage Should Be Within    ${voltage}    ${VOLTAGE_TOLERANCE}

KW-050 Load Current Should Be Within
    ${current}=    Get Load Current
    Load Current Should Be Within    ${current}    ${CURRENT_TOLERANCE}

KW-051 Load Power Should Be Within
    ${power}=    Get Load Power
    Load Power Should Be Within    ${power}    ${POWER_TOLERANCE}

KW-052 Load Should Report No Protection Faults
    ${reading}=    Load Should Report No Protection Faults
    Should Be Empty    ${reading}[active_protections]

KW-053 Load Input State Should Be
    Load Input Off
    Load Input State Should Be    OFF

KW-054 Load Mode Should Be
    Set Load Mode    CC
    Load Mode Should Be    CC

KW-055 Get Load Connection Info
    ${info}=    Get Load Connection Info
    Should Be Equal    ${info}[alias]    ${HARDWARE_ALIAS}
    Should Contain    ${info}[transport]    ${PORT}
    Should Contain    ${info}[open_aliases]    ${HARDWARE_ALIAS}
    Log Dictionary    ${info}

KW-056 Is Connected
    [Documentation]    RFDS-002 generic connection query, both for the active alias and an unknown one.
    ${connected}=    Is Connected
    Should Be Equal    ${connected}    ${TRUE}
    ${unknown}=    Is Connected    does-not-exist
    Should Be Equal    ${unknown}    ${FALSE}

KW-057 Get Connection State
    [Documentation]    RFDS-002 generic normalized connection-state dictionary.
    ${state}=    Get Connection State
    Should Be Equal    ${state}[alias]    ${HARDWARE_ALIAS}
    Should Be Equal    ${state}[connected]    ${TRUE}
    Should Be Equal    ${state}[state]    connected
    Log Dictionary    ${state}

KW-058 Check Communication
    [Documentation]    RFDS-002 generic bounded, non-destructive communication check.
    ${ok}=    Check Communication
    Should Be Equal    ${ok}    ${TRUE}

KW-059 Get Identity
    [Documentation]    RFDS-002 generic stable identity string.
    ${identity}=    Get Identity
    Should Not Be Empty    ${identity}
    Log    ${identity}

KW-060 Connect And Disconnect
    [Documentation]    RFDS-002 generic connect/disconnect, idempotent, exercised against a simulated secondary alias.
    ${state}=    Connect    alias=${SECONDARY_ALIAS}    simulated=${TRUE}    model=${MODEL}
    Should Be Equal    ${state}[alias]    ${SECONDARY_ALIAS}
    Should Be Equal    ${state}[connected]    ${TRUE}
    ${same_state}=    Connect    alias=${SECONDARY_ALIAS}    simulated=${TRUE}    model=${MODEL}
    Should Be Equal    ${state}    ${same_state}
    Disconnect    ${SECONDARY_ALIAS}
    Disconnect    ${SECONDARY_ALIAS}
    Switch Load Connection    ${HARDWARE_ALIAS}

KW-004 Close All Load Connections
    [Documentation]    This final test closes every connection, verifies the disconnected state, then reopens hardware for suite teardown.
    Close All Load Connections
    Run Keyword And Expect Error    *No DC load connection is open*    Get Load Connection Info
    Open Load Connection    port=${PORT}    baudrate=${BAUDRATE}
    ...    model=${MODEL}    alias=${HARDWARE_ALIAS}    address=${ADDRESS}
    ...    timeout=${TIMEOUT}    simulated=${FALSE}    identify=${TRUE}

*** Keywords ***
Initialize Hardware Conformance
    Capture Software Evidence
    Open Hardware Load

Capture Software Evidence
    ${source_version}=    Evaluate    bk8500_load.VERSION    modules=bk8500_load
    ${distribution_version}=    Evaluate    importlib.metadata.version("bk8500-load")    modules=importlib.metadata
    ${robot_version}=    Evaluate    robot.__version__    modules=robot
    ${python_version}=    Evaluate    platform.python_version()    modules=platform
    ${platform_name}=    Evaluate    platform.platform()    modules=platform
    Set Suite Metadata    Driver source version    ${source_version}
    Set Suite Metadata    Installed distribution version    ${distribution_version}
    Set Suite Metadata    Robot Framework version    ${robot_version}
    Set Suite Metadata    Python version    ${python_version}
    Set Suite Metadata    Host platform    ${platform_name}
    Log To Console    Driver source=${source_version}; installed=${distribution_version}; Robot=${robot_version}; Python=${python_version}
    Should Be Equal    ${source_version}    ${EXPECTED_DRIVER_VERSION}
    ...    Source package version ${source_version} does not match suite release ${EXPECTED_DRIVER_VERSION}.
    Should Be Equal    ${distribution_version}    ${source_version}
    ...    Installed bk8500-load ${distribution_version} does not match imported source ${source_version}; reinstall the release wheel.

Open Hardware Load
    Log    Opening real BK8500 load on ${PORT}; preferred baud=${BAUDRATE}; auto-detect=${AUTO_DETECT_BAUDRATE}; address=${ADDRESS}.
    Open Load Connection    port=${PORT}    baudrate=${BAUDRATE}
    ...    model=${MODEL}    alias=${HARDWARE_ALIAS}    address=${ADDRESS}
    ...    timeout=${TIMEOUT}    simulated=${FALSE}    identify=${TRUE}
    ...    auto_detect_baudrate=${AUTO_DETECT_BAUDRATE}
    ...    baudrate_candidates=${BAUDRATE_CANDIDATES}    probe_timeout=${PROBE_TIMEOUT}
    ${connection}=    Get Load Connection Info
    Log Dictionary    ${connection}
    ${identity}=    Get Load Product Information
    Log Dictionary    ${identity}
    Set Suite Metadata    Instrument model    ${identity}[model]
    Set Suite Metadata    Instrument serial number    ${identity}[serial_number]
    Set Suite Metadata    Instrument firmware version    ${identity}[firmware_version]
    Set Suite Metadata    Hardware transport    ${PORT} at ${connection}[baudrate] baud, address ${ADDRESS}
    Set Suite Metadata    Baud auto-detection    ${connection}[baudrate_auto_detected]
    Claim Remote Control
    Load Input Off
    Set Load Function    FIXED

Prepare Hardware For Keyword Test
    Switch Load Connection    ${HARDWARE_ALIAS}
    Claim Remote Control
    Load Input Off
    Set Load Function    FIXED

Per Test Safe Teardown
    Run Keyword And Ignore Error    Switch Load Connection    ${HARDWARE_ALIAS}
    Run Keyword And Ignore Error    Claim Remote Control
    Run Keyword And Ignore Error    Load Input Off
    Run Keyword And Ignore Error    Set Load Function    FIXED
    Run Keyword And Ignore Error    Set Local Key Enabled    ${TRUE}

Final Safe Teardown
    Run Keyword And Ignore Error    Switch Load Connection    ${HARDWARE_ALIAS}
    Run Keyword And Ignore Error    Reset Load To Safe State
    Close All Load Connections

Numbers Should Be Close
    [Arguments]    ${actual}    ${expected}    ${tolerance}
    ${difference}=    Evaluate    abs(float($actual) - float($expected))
    Should Be True    ${difference} <= ${tolerance}
    ...    Difference ${difference} exceeds tolerance ${tolerance}; actual=${actual}, expected=${expected}
