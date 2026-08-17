*** Settings ***
Documentation    Demonstrates explicit safe shutdown using the simulator.
Library          rf_votsch_climate_chamber.VotschClimateChamberLibrary
Suite Setup      Connect    resource=SIM::safe-shutdown    alias=default
Suite Teardown   Disconnect All

*** Test Cases ***
Put Chamber Into Safe State
    Set Dryer    ${TRUE}
    Set Compressed Air    ${TRUE}
    Set Fan    ${TRUE}
    Start Chamber
    ${result}=    Safe Shutdown
    Should Be True    ${result}[safe]
    Chamber Should Be Stopped
    # Safe Shutdown reports per-output outcomes under "actions"; there are no
    # top-level "dryer"/"compressed_air" keys.
    ${statuses}=    Evaluate    {a['action']: a['status'] for a in $result['actions']}
    Should Be Equal    ${statuses}[dryer_off]    PASS
    Should Be Equal    ${statuses}[compressed_air_off]    PASS
    Should Be Equal    ${statuses}[fan_off]    PASS
    Should Be Equal    ${statuses}[chamber_stop]    PASS
    ${dryer}=    Get Dryer
    ${air}=      Get Compressed Air
    ${fan}=      Get Fan
    Should Not Be True    ${dryer}
    Should Not Be True    ${air}
    Should Not Be True    ${fan}
