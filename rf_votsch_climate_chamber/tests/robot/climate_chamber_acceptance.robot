*** Settings ***
Documentation     Acceptance tests use the built-in protocol simulator; no hardware is required.
Library           rf_votsch_climate_chamber.VotschClimateChamberLibrary
Suite Setup       Connect    resource=SIM::acceptance    alias=default    temperature_min_c=-40    temperature_max_c=180
Suite Teardown    Disconnect All

*** Test Cases ***
Read Identification And Diagnostics
    ${identity}=    Get Identity
    Should Contain    ${identity}    SIM-2604
    ${diagnostics}=    Get Diagnostics
    Should Be Equal    ${diagnostics}[sessions][0][diagnostics][chamber_status]    READY

Set And Verify Temperature
    Set Temperature    85
    Temperature Setpoint Should Be    85

Start Stabilize And Stop
    Start Chamber
    Chamber Should Be Running
    ${final}=    Wait For Temperature Stability
    ...    target_c=85
    ...    tolerance_c=0.1
    ...    stable_samples=2
    ...    poll_interval_s=1 ms
    ...    settle_timeout_s=1 s
    Should Be Equal As Numbers    ${final}    85
    Stop Chamber
    Chamber Should Be Stopped

Control Auxiliary Outputs
    Set Dryer    ON
    Set Compressed Air    TRUE
    ${dryer}=    Get Dryer
    ${air}=    Get Compressed Air
    Should Be True    ${dryer}
    Should Be True    ${air}

Read Communication Statistics
    ${diagnostics}=    Get Diagnostics
    Should Be True    ${diagnostics}[sessions][0][transport_metrics][commands_ok] > 0

Reconnect Session
    Reconnect
    Connection Should Be Available
