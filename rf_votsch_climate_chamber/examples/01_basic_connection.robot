*** Settings ***
Documentation    RFDS-002 universal lifecycle and identity example.
Library    rf_votsch_climate_chamber.library.VotschClimateChamberLibrary
Suite Teardown    Disconnect All

*** Test Cases ***
Connect Identify And Disconnect
    ${state}=    Connect    resource=SIM::default
    Should Be True    ${state}[connected]
    ${identity}=    Get Identity    refresh=${TRUE}
    Log    ${identity}
    Disconnect
