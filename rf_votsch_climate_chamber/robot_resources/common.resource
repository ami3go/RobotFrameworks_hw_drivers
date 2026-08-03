*** Settings ***
Documentation    Shared RFDS Vötsch climate chamber resource.
Library    rf_votsch_climate_chamber.VotschClimateChamberLibrary

*** Keywords ***
Connect Simulator Chamber
    [Arguments]    ${alias}=default
    ${state}=    Connect    resource=SIM::default    alias=${alias}
    RETURN    ${state}

Safe Chamber Teardown
    Run Keyword And Ignore Error    Safe Shutdown
    Run Keyword And Ignore Error    Disconnect All
