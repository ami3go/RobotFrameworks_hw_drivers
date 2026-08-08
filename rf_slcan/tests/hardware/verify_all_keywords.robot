*** Settings ***
Documentation     RFDS-019 real-hardware conformance: exercises every public keyword of
...               rf_slcan.SlcanLibrary against a physical SLCAN interface adapter and
...               verifies its response. Does not run automatically in CI (Force Tags
...               "hardware"; exclude with `--exclude hardware` in automated pipelines).
...
...               Requires RESOURCE (a real serial port, e.g. /dev/ttyACM0 or COM5) — there
...               is no safe default, so Suite Setup fails immediately with a clear message
...               if it is left empty.
...
...               The channel stays CLOSED (never opened) unless ALLOW_OPEN is set, since
...               opening a channel already configures the adapter for bus participation.
...               Frame transmission additionally requires ALLOW_TRANSMIT — Send Frame puts
...               a real frame on a real CAN bus, which can disrupt other ECUs/devices
...               sharing it, so this only runs against a bench known to tolerate test
...               traffic. Without ALLOW_TRANSMIT, the channel (if opened at all) is opened
...               LISTEN_ONLY so receive-path keywords can still be exercised passively.
...               Suite Teardown always closes the channel and disconnects, whatever state
...               a test case left things in.
Library           rf_slcan.SlcanLibrary
Library           Collections
Library           OperatingSystem
Suite Setup       Initialize Hardware Conformance
Suite Teardown    Final Safe Teardown
Test Setup        Prepare Adapter For Keyword Test
Test Teardown     Per Test Safe Teardown
Force Tags        hardware    slcan    keyword-conformance

*** Variables ***
${RESOURCE}                  ${EMPTY}
${ALIAS}                     hardware
${SECONDARY_ALIAS}           secondary
${BITRATE}                   500K
${ALLOW_OPEN}                ${FALSE}
${ALLOW_TRANSMIT}            ${FALSE}
${TEST_ARBITRATION_ID}       ${0x123}
${EXPECTED_DRIVER_VERSION}    26.2

*** Test Cases ***
# ----------------------------------------------------------------------
# Connection (RFDS-002)
# ----------------------------------------------------------------------
KW-001 Connect
    [Documentation]    Reopen the real connection and verify the normalized
    ...    connection-state dictionary Connect returns.
    Disconnect    ${ALIAS}
    ${state}=    Open Hardware Connection
    Should Be Equal    ${state}[alias]    ${ALIAS}
    Should Be Equal    ${state}[connected]    ${TRUE}
    Should Be Equal    ${state}[state]    connected
    Should Not Be Empty    ${state}[resource]

KW-002 Disconnect
    [Documentation]    Idempotent: closing an already-closed alias must not raise.
    Connect    alias=${SECONDARY_ALIAS}    simulated=${TRUE}
    Disconnect    ${SECONDARY_ALIAS}
    Disconnect    ${SECONDARY_ALIAS}
    ${connected}=    Is Connected    ${SECONDARY_ALIAS}
    Should Be Equal    ${connected}    ${FALSE}

KW-003 Is Connected
    ${connected}=    Is Connected    ${ALIAS}
    Should Be Equal    ${connected}    ${TRUE}
    ${unknown}=    Is Connected    does-not-exist
    Should Be Equal    ${unknown}    ${FALSE}

KW-004 Get Connection State
    ${state}=    Get Connection State    alias=${ALIAS}    refresh=${TRUE}
    Should Be Equal    ${state}[alias]    ${ALIAS}
    Should Be Equal    ${state}[connected]    ${TRUE}
    Should Be Equal    ${state}[communication_ok]    ${TRUE}
    Log Dictionary    ${state}

KW-005 Check Communication
    ${ok}=    Check Communication    ${ALIAS}
    Should Be Equal    ${ok}    ${TRUE}

KW-006 Get Identity
    ${identity}=    Get Identity    alias=${ALIAS}    refresh=${TRUE}
    Should Not Be Empty    ${identity}
    Should Contain    ${identity}    SLCAN
    Log    ${identity}

KW-007 Switch Adapter
    Connect    alias=${SECONDARY_ALIAS}    simulated=${TRUE}
    ${active}=    Switch Adapter    ${SECONDARY_ALIAS}
    Should Be Equal    ${active}    ${SECONDARY_ALIAS}
    Switch Adapter    ${ALIAS}
    Disconnect    ${SECONDARY_ALIAS}

KW-008 Get Active Adapter
    ${active}=    Get Active Adapter
    Should Be Equal    ${active}    ${ALIAS}

KW-009 List Adapter Connections
    Connect    alias=${SECONDARY_ALIAS}    simulated=${TRUE}
    ${connections}=    List Adapter Connections
    List Should Contain Value    ${connections}    ${ALIAS}
    List Should Contain Value    ${connections}    ${SECONDARY_ALIAS}
    Disconnect    ${SECONDARY_ALIAS}

# ----------------------------------------------------------------------
# Channel control
# ----------------------------------------------------------------------
KW-010 Set Bitrate
    [Documentation]    Rejected by the adapter while the channel is open (task-documented
    ...    constraint), so this always runs with the channel closed first.
    Close Channel    ${ALIAS}
    Set Bitrate    ${BITRATE}    ${ALIAS}

KW-011 Open Channel
    [Documentation]    Skipped unless ALLOW_OPEN is set. Opens LISTEN_ONLY unless
    ...    ALLOW_TRANSMIT is also set, since NORMAL mode configures the adapter as an
    ...    active bus participant (ack-capable) even before this suite sends anything.
    Skip If    not ${ALLOW_OPEN}    Set ALLOW_OPEN:true to exercise Open Channel.
    ${mode}=    Set Variable If    ${ALLOW_TRANSMIT}    NORMAL    LISTEN_ONLY
    Open Channel    ${mode}    ${ALIAS}
    ${is_open}=    Is Channel Open    ${ALIAS}
    Should Be Equal    ${is_open}    ${TRUE}

KW-012 Close Channel
    [Documentation]    Always safe and always exercised — closing must always be possible
    ...    per this driver's own safety notes, regardless of ALLOW_OPEN.
    Close Channel    ${ALIAS}
    ${is_open}=    Is Channel Open    ${ALIAS}
    Should Be Equal    ${is_open}    ${FALSE}

KW-013 Is Channel Open
    Close Channel    ${ALIAS}
    ${is_open}=    Is Channel Open    ${ALIAS}
    Should Be Equal    ${is_open}    ${FALSE}

# ----------------------------------------------------------------------
# Acceptance filter (Gate 3) — M/m rejected while channel is open, same as Set Bitrate.
# ----------------------------------------------------------------------
KW-014 Set Acceptance Code
    Close Channel    ${ALIAS}
    Set Acceptance Code    0x000    ${ALIAS}

KW-015 Get Acceptance Code
    Close Channel    ${ALIAS}
    Set Acceptance Code    0x000    ${ALIAS}
    ${code}=    Get Acceptance Code    ${ALIAS}
    Should Be Equal As Integers    ${code}    0

KW-016 Set Acceptance Mask
    Close Channel    ${ALIAS}
    Set Acceptance Mask    0xFFFFFFFF    ${ALIAS}

KW-017 Get Acceptance Mask
    Close Channel    ${ALIAS}
    Set Acceptance Mask    0xFFFFFFFF    ${ALIAS}
    ${mask}=    Get Acceptance Mask    ${ALIAS}
    Should Be Equal As Integers    ${mask}    4294967295

# ----------------------------------------------------------------------
# Timestamp mode (Gate 3)
# ----------------------------------------------------------------------
KW-018 Set Timestamps Enabled
    Set Timestamps Enabled    ${TRUE}    ${ALIAS}
    ${enabled}=    Get Timestamps Enabled    ${ALIAS}
    Should Be Equal    ${enabled}    ${TRUE}
    Set Timestamps Enabled    ${FALSE}    ${ALIAS}

KW-019 Get Timestamps Enabled
    ${enabled}=    Get Timestamps Enabled    ${ALIAS}
    Should Be True    $enabled is True or $enabled is False

# ----------------------------------------------------------------------
# Frames
# ----------------------------------------------------------------------
KW-020 Send Frame
    [Documentation]    Requires both ALLOW_OPEN and ALLOW_TRANSMIT — puts a real frame on
    ...    a real CAN bus. See suite Documentation.
    Skip If    not (${ALLOW_OPEN} and ${ALLOW_TRANSMIT})
    ...    Set ALLOW_OPEN:true and ALLOW_TRANSMIT:true to exercise Send Frame.
    Open Channel    NORMAL    ${ALIAS}
    Send Frame    ${TEST_ARBITRATION_ID}    AABBCC    alias=${ALIAS}
    Close Channel    ${ALIAS}

KW-021 Receive Frame
    [Documentation]    Passive: waits briefly for whatever the bus naturally carries.
    ...    ${None} on nothing arriving is a normal, passing outcome (task-documented).
    Skip If    not ${ALLOW_OPEN}    Set ALLOW_OPEN:true to exercise Receive Frame.
    Open Channel    LISTEN_ONLY    ${ALIAS}
    ${frame}=    Receive Frame    timeout_s=${1.0}    alias=${ALIAS}
    Log    ${frame}
    Close Channel    ${ALIAS}

KW-022 Drain Received Frames
    Skip If    not ${ALLOW_OPEN}    Set ALLOW_OPEN:true to exercise Drain Received Frames.
    Open Channel    LISTEN_ONLY    ${ALIAS}
    Sleep    ${0.2}
    ${frames}=    Drain Received Frames    alias=${ALIAS}
    Should Be True    isinstance($frames, list)
    Close Channel    ${ALIAS}

KW-023 Get Received Frame Count
    ${count}=    Get Received Frame Count    ${ALIAS}
    Should Be True    ${count} >= 0

KW-024 Clear Received Frames
    Clear Received Frames    ${ALIAS}
    ${count}=    Get Received Frame Count    ${ALIAS}
    Should Be Equal As Integers    ${count}    0

KW-025 Get Receive Overflow Count
    ${count}=    Get Receive Overflow Count    ${ALIAS}
    Should Be True    ${count} >= 0

# ----------------------------------------------------------------------
# Status / identity queries
# ----------------------------------------------------------------------
KW-026 Get Status
    ${status}=    Get Status    ${ALIAS}
    Dictionary Should Contain Key    ${status}    bus_error
    Dictionary Should Contain Key    ${status}    raw_flags
    Log Dictionary    ${status}

KW-027 Get Version
    ${version}=    Get Version    ${ALIAS}
    Should Not Be Empty    ${version}
    Log    ${version}

KW-028 Get Serial Number
    ${serial}=    Get Serial Number    ${ALIAS}
    Should Not Be Empty    ${serial}
    Log    ${serial}

# ----------------------------------------------------------------------
# Raw escape hatch
# ----------------------------------------------------------------------
KW-029 Enable Raw SLCAN
    [Documentation]    Requires the exact confirmation text; enabled state then persists
    ...    for the rest of this suite's connection, so KW-030 relies on it already being
    ...    enabled here rather than re-enabling it itself.
    Enable Raw SLCAN    ENABLE RAW SLCAN    ${ALIAS}

KW-030 Raw SLCAN Command
    [Documentation]    ``V`` (version query) is universal and non-mutating — safe on any
    ...    SLCAN adapter and a good proof that the raw escape hatch round-trips real
    ...    adapter responses.
    ${response}=    Raw SLCAN Command    V    expects_data=${TRUE}    alias=${ALIAS}
    Should Not Be Empty    ${response}
    Log    ${response}

# ----------------------------------------------------------------------
# Diagnostics
# ----------------------------------------------------------------------
KW-031 Export Diagnostic Bundle
    ${path}=    Export Diagnostic Bundle
    Should Not Be Empty    ${path}
    File Should Exist    ${path}
    Log    Diagnostic bundle written to ${path}

*** Keywords ***
Initialize Hardware Conformance
    Require Real Resource
    Capture Software Evidence
    Open Hardware Connection
    Close Channel    ${ALIAS}
    Set Bitrate    ${BITRATE}    ${ALIAS}

Require Real Resource
    Should Not Be Equal    ${RESOURCE}    ${EMPTY}
    ...    Pass a real serial port: -v RESOURCE:/dev/ttyACM0 (or -v RESOURCE:COM5 on Windows)

Capture Software Evidence
    ${source_version}=    Evaluate    slcan.__version__    modules=slcan
    ${distribution_version}=    Evaluate
    ...    importlib.metadata.version("robotframework-slcan")    modules=importlib.metadata
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
    ...    Installed robotframework-slcan ${distribution_version} does not match imported source ${source_version}; reinstall the release wheel.

Open Hardware Connection
    Log    Opening real SLCAN adapter on resource=${RESOURCE}.
    ${state}=    Connect    resource=${RESOURCE}    alias=${ALIAS}
    RETURN    ${state}

Prepare Adapter For Keyword Test
    Run Keyword And Ignore Error    Switch Adapter    ${ALIAS}
    Run Keyword And Ignore Error    Close Channel    ${ALIAS}

Per Test Safe Teardown
    Run Keyword And Ignore Error    Switch Adapter    ${ALIAS}
    Run Keyword And Ignore Error    Close Channel    ${ALIAS}

Final Safe Teardown
    Run Keyword And Ignore Error    Switch Adapter    ${ALIAS}
    Run Keyword And Ignore Error    Close Channel    ${ALIAS}
    Run Keyword And Ignore Error    Disconnect    ${ALIAS}
