*** Settings ***
Documentation    Explicit reconnect and post-recovery communication check.
Library    rf_votsch_climate_chamber.library.VotschClimateChamberLibrary
Suite Setup    Connect    SIM::default
Suite Teardown    Disconnect All

*** Test Cases ***
Reconnect And Verify
    ${state}=    Reconnect
    Should Be True    ${state}[connected]
    ${ok}=    Check Communication
    Should Be True    ${ok}
