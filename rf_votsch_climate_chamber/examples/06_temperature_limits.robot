*** Settings ***
Documentation    Local pre-transmission temperature safety limits.
Library    rf_votsch_climate_chamber.VotschClimateChamberLibrary
Library    Collections
Suite Setup    Connect    SIM::default
Suite Teardown    Disconnect All

*** Test Cases ***
Inspect And Tighten Limits
    ${original}=    Get Temperature Limits
    Log Dictionary    ${original}
    ${limits}=    Set Temperature Limits    -20    100
    Should Be Equal As Numbers    ${limits}[min]    -20
