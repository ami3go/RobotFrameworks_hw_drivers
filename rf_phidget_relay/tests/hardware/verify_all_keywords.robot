*** Settings ***
Documentation     RFDS-019 real-hardware conformance: exercises every public keyword of
...               rf_phidget_relay.PhidgetRelayLibrary against two physical
...               PhidgetInterfaceKit 0/0/4 boards and verifies the response. Does not run
...               automatically in CI (Force Tags "hardware"; exclude with `--exclude
...               hardware` in automated pipelines).
...
...               Requires DEVICE_A_SERIAL/DEVICE_B_SERIAL (see Variables below) — there is
...               no safe default serial number, so Suite Setup fails immediately with a
...               clear message if they are left at their placeholder value.
...
...               Every relay stays OPEN for the whole suite unless ALLOW_CLOSE is set, and
...               Close All Relays additionally requires ALLOW_CLOSE_ALL — closing all eight
...               channels at once is explicitly called out as unsafe-unless-proven in this
...               driver's own RFDS-017 contract (ai/phidget_relay_ai_contract.yaml,
...               safety_rules.forbidden) since it may connect two external sources through
...               the relay bank without any interlock. Only set these against a bench whose
...               wiring is known safe for every channel to be closed, alone or together.
...               Test Teardown and Suite Teardown always attempt Open All Relays regardless
...               of how a test case left the bank.
Library           rf_phidget_relay.PhidgetRelayLibrary
Library           Collections
Library           OperatingSystem
Suite Setup       Initialize Hardware Conformance
Suite Teardown    Final Safe Teardown
Test Setup        Prepare Relay Bank For Keyword Test
Test Teardown     Per Test Safe Teardown
Force Tags        hardware    phidget_relay    keyword-conformance

*** Variables ***
${DEVICE_A_SERIAL}          0
${DEVICE_B_SERIAL}          0
${TEST_CHANNEL}             ${1}
${ALLOW_CLOSE}               ${FALSE}
${ALLOW_CLOSE_ALL}           ${FALSE}
${EXPECTED_DRIVER_VERSION}    26.3

*** Test Cases ***
# ----------------------------------------------------------------------
# Connection
# ----------------------------------------------------------------------
KW-001 Connect Relays
    [Documentation]    Reopen the real connection and verify the resulting connection status
    ...    and the fixed logical-to-physical mapping.
    Disconnect Relays
    Connect Relays    ${DEVICE_A_SERIAL}    ${DEVICE_B_SERIAL}
    ${status}=    Get Connection Status
    Should Be Equal    ${status}    CONNECTED
    ${mapping}=    Get Relay Mapping
    Should Be Equal As Strings    ${mapping}[1]    serial=${DEVICE_A_SERIAL}, output=0

KW-002 Disconnect Relays
    [Documentation]    Reconnects immediately afterward — this suite's single library
    ...    instance is shared across every remaining test case (RFDS-002 SUITE scope).
    Disconnect Relays
    ${status}=    Get Connection Status
    Should Be Equal    ${status}    DISCONNECTED
    Connect Relays    ${DEVICE_A_SERIAL}    ${DEVICE_B_SERIAL}
    ${status}=    Get Connection Status
    Should Be Equal    ${status}    CONNECTED

# ----------------------------------------------------------------------
# Single-channel control
# ----------------------------------------------------------------------
KW-003 Set Relay State
    Set Relay State    ${TEST_CHANNEL}    ${FALSE}
    ${state}=    Get Relay State    ${TEST_CHANNEL}
    Should Be Equal    ${state}    OPEN
    IF    ${ALLOW_CLOSE}
        Set Relay State    ${TEST_CHANNEL}    ${TRUE}
        ${state}=    Get Relay State    ${TEST_CHANNEL}
        Should Be Equal    ${state}    CLOSED
        Set Relay State    ${TEST_CHANNEL}    ${FALSE}
    END

KW-004 Open Relay
    Open Relay    ${TEST_CHANNEL}
    Relay Should Be Open    ${TEST_CHANNEL}

KW-005 Close Relay
    Skip If    not ${ALLOW_CLOSE}    Set ALLOW_CLOSE:true to exercise Close Relay.
    Close Relay    ${TEST_CHANNEL}
    Relay Should Be Closed    ${TEST_CHANNEL}
    Open Relay    ${TEST_CHANNEL}

KW-006 Get Relay State
    ${state}=    Get Relay State    ${TEST_CHANNEL}
    Should Contain Any    ${state}    OPEN    CLOSED

KW-007 Relay Should Be Open
    Open Relay    ${TEST_CHANNEL}
    Relay Should Be Open    ${TEST_CHANNEL}

KW-008 Relay Should Be Closed
    Skip If    not ${ALLOW_CLOSE}    Set ALLOW_CLOSE:true to exercise Relay Should Be Closed.
    Close Relay    ${TEST_CHANNEL}
    Relay Should Be Closed    ${TEST_CHANNEL}
    Open Relay    ${TEST_CHANNEL}

# ----------------------------------------------------------------------
# Whole-bank control
# ----------------------------------------------------------------------
KW-009 Open All Relays
    Open All Relays
    ${states}=    Get All Relay States
    FOR    ${channel}    ${state}    IN    &{states}
        Should Be Equal    ${state}    OPEN
    END

KW-010 Close All Relays
    [Documentation]    Requires both ALLOW_CLOSE and ALLOW_CLOSE_ALL — see suite
    ...    Documentation. Always reopens every channel before returning, success or not.
    Skip If    not (${ALLOW_CLOSE} and ${ALLOW_CLOSE_ALL})
    ...    Set ALLOW_CLOSE:true and ALLOW_CLOSE_ALL:true to exercise Close All Relays.
    TRY
        Close All Relays
        ${states}=    Get All Relay States
        FOR    ${channel}    ${state}    IN    &{states}
            Should Be Equal    ${state}    CLOSED
        END
    FINALLY
        Open All Relays
    END

KW-011 Set Relay Pattern
    [Documentation]    Closes only TEST_CHANNEL (a single-channel-equivalent risk) when
    ...    ALLOW_CLOSE is set; an all-OPEN pattern is exercised either way.
    ${open_pattern}=    Set Variable    00000000
    Set Relay Pattern    ${open_pattern}
    ${states}=    Get All Relay States
    FOR    ${channel}    ${state}    IN    &{states}
        Should Be Equal    ${state}    OPEN
    END
    IF    ${ALLOW_CLOSE}
        ${pattern}=    Build Single Channel Pattern    ${TEST_CHANNEL}
        Set Relay Pattern    ${pattern}
        Relay Should Be Closed    ${TEST_CHANNEL}
        Set Relay Pattern    ${open_pattern}
    END

KW-012 Set Multiple Relays
    ${open_states}=    Create Dictionary    ${TEST_CHANNEL}=${FALSE}
    Set Multiple Relays    ${open_states}
    Relay Should Be Open    ${TEST_CHANNEL}
    IF    ${ALLOW_CLOSE}
        ${closed_states}=    Create Dictionary    ${TEST_CHANNEL}=${TRUE}
        Set Multiple Relays    ${closed_states}
        Relay Should Be Closed    ${TEST_CHANNEL}
        Set Multiple Relays    ${open_states}
    END

KW-013 Get All Relay States
    ${states}=    Get All Relay States
    Length Should Be    ${states}    8
    Dictionary Should Contain Key    ${states}    1
    Dictionary Should Contain Key    ${states}    8

KW-014 Pulse Relay
    [Documentation]    Momentarily closes TEST_CHANNEL, so gated the same as Close Relay.
    Skip If    not ${ALLOW_CLOSE}    Set ALLOW_CLOSE:true to exercise Pulse Relay.
    Pulse Relay    ${TEST_CHANNEL}    ${0.2}
    Relay Should Be Open    ${TEST_CHANNEL}

# ----------------------------------------------------------------------
# Identity and diagnostics
# ----------------------------------------------------------------------
KW-015 Get Relay Mapping
    ${mapping}=    Get Relay Mapping
    Length Should Be    ${mapping}    8
    Should Be Equal As Strings    ${mapping}[1]    serial=${DEVICE_A_SERIAL}, output=0
    Should Be Equal As Strings    ${mapping}[5]    serial=${DEVICE_B_SERIAL}, output=0

KW-016 Get Connection Status
    ${status}=    Get Connection Status
    Should Be Equal    ${status}    CONNECTED

KW-017 Get Driver Information
    ${info}=    Get Driver Information
    Should Be Equal As Strings    ${info}[version]    ${EXPECTED_DRIVER_VERSION}
    Should Be Equal    ${info}[connection_status]    CONNECTED
    Log Dictionary    ${info}

KW-018 Emergency Open All Relays
    Emergency Open All Relays
    ${states}=    Get All Relay States
    FOR    ${channel}    ${state}    IN    &{states}
        Should Be Equal    ${state}    OPEN
    END

KW-019 Export Diagnostic Bundle
    ${path}=    Export Diagnostic Bundle
    Should Not Be Empty    ${path}
    File Should Exist    ${path}
    Log    Diagnostic bundle written to ${path}

*** Keywords ***
Initialize Hardware Conformance
    Require Real Serial Numbers
    Capture Software Evidence
    Connect Relays    ${DEVICE_A_SERIAL}    ${DEVICE_B_SERIAL}
    ${mapping}=    Get Relay Mapping
    Log Dictionary    ${mapping}
    Open All Relays

Require Real Serial Numbers
    [Documentation]    0 is never a valid Phidget serial number (PhidgetRelayConfigurationError
    ...    would catch it too, but this fails faster with a clearer message).
    Should Not Be Equal As Integers    ${DEVICE_A_SERIAL}    0
    ...    Pass real Phidget serial numbers: -v DEVICE_A_SERIAL:<n> -v DEVICE_B_SERIAL:<n>
    Should Not Be Equal As Integers    ${DEVICE_B_SERIAL}    0
    ...    Pass real Phidget serial numbers: -v DEVICE_A_SERIAL:<n> -v DEVICE_B_SERIAL:<n>

Capture Software Evidence
    ${source_version}=    Evaluate    rf_phidget_relay.__version__    modules=rf_phidget_relay
    ${distribution_version}=    Evaluate
    ...    importlib.metadata.version("rf-phidget-relay")    modules=importlib.metadata
    ${robot_version}=    Evaluate    robot.__version__    modules=robot
    ${python_version}=    Evaluate    platform.python_version()    modules=platform
    ${platform_name}=    Evaluate    platform.platform()    modules=platform
    Set Suite Metadata    Driver source version    ${source_version}
    Set Suite Metadata    Installed distribution version    ${distribution_version}
    Set Suite Metadata    Robot Framework version    ${robot_version}
    Set Suite Metadata    Python version    ${python_version}
    Set Suite Metadata    Host platform    ${platform_name}
    Log To Console
    ...    Driver source=${source_version}; installed=${distribution_version}; Robot=${robot_version}; Python=${python_version}
    Should Be Equal    ${source_version}    ${EXPECTED_DRIVER_VERSION}
    ...    Source package version ${source_version} does not match suite release ${EXPECTED_DRIVER_VERSION}.
    Should Be Equal    ${distribution_version}    ${source_version}
    ...    Installed rf-phidget-relay ${distribution_version} does not match imported source ${source_version}; reinstall the release wheel.

Build Single Channel Pattern
    [Documentation]    Returns an 8-digit pattern with only the given 1-indexed logical
    ...    channel set to CLOSED ("1"), matching Set Relay Pattern's "leftmost digit is CH1"
    ...    convention.
    [Arguments]    ${channel}
    ${digits}=    Evaluate    ["1" if i == $channel else "0" for i in range(1, 9)]
    ${pattern}=    Evaluate    "".join($digits)
    RETURN    ${pattern}

Prepare Relay Bank For Keyword Test
    ${status}=    Get Connection Status
    IF    "${status}" != "CONNECTED"
        Connect Relays    ${DEVICE_A_SERIAL}    ${DEVICE_B_SERIAL}
    END
    Open All Relays

Per Test Safe Teardown
    Run Keyword And Ignore Error    Open All Relays

Final Safe Teardown
    Run Keyword And Ignore Error    Emergency Open All Relays
    Run Keyword And Ignore Error    Disconnect Relays
