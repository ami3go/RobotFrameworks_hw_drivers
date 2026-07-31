*** Settings ***
Documentation     Acceptance tests use a local protocol simulator; no hardware is required.
Library           votsch_climate_chamber.robot_library.VotschClimateChamberLibrary    progress_log_interval=1 ms
Library           tests.support.FakeChamberControl
Suite Setup       Start Test Environment
Suite Teardown    Stop Test Environment

*** Variables ***
${MIN_TEMP}       -40
${MAX_TEMP}       180

*** Test Cases ***
Read Identification And Health
    ${idn}=    Get Climate Chamber Identification
    Should Contain    ${idn}    FAKE-2601
    ${health}=    Get Climate Chamber Health
    Should Be Equal    ${health}[chamber_status]    READY

Set And Verify Temperature
    Set Climate Chamber Temperature    85
    Climate Chamber Setpoint Should Be    85

Start Stabilize And Stop
    Start Climate Chamber
    Climate Chamber Should Be Running
    ${final}=    Wait Until Climate Chamber Is Stable
    ...    target=85
    ...    tolerance=0.1
    ...    poll_interval=1 ms
    ...    timeout=1 s
    ...    stable_samples=2
    Should Be Equal As Numbers    ${final}    85
    Stop Climate Chamber
    Climate Chamber Should Be Stopped

Control Auxiliary Outputs
    ${dryer}=    Set Climate Chamber Dryer    ON
    ${air}=      Set Climate Chamber Compressed Air    TRUE
    Should Be True    ${dryer}
    Should Be True    ${air}

Read Communication Statistics
    ${stats}=    Get Climate Chamber Connection Statistics
    Should Be True    ${stats}[commands_ok] > 0

Reconnect Session
    Reconnect Climate Chamber
    Climate Chamber Should Be Connected

*** Keywords ***
Start Test Environment
    ${port}=    Start Fake Chamber
    Connect Climate Chamber
    ...    127.0.0.1
    ...    ${MIN_TEMP}
    ...    ${MAX_TEMP}
    ...    port=${port}
    ...    timeout=500 ms
    ...    response_timeout=500 ms

Stop Test Environment
    Run Keyword And Ignore Error    Stop And Disconnect Climate Chamber
    Stop Fake Chamber
