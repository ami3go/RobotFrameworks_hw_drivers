*** Settings ***
Documentation    Heating and cooling gradient control.
Library    rf_votsch_climate_chamber.library.VotschClimateChamberLibrary
Suite Setup    Connect    SIM::default
Suite Teardown    Run Keywords    Safe Shutdown    AND    Disconnect All

*** Test Cases ***
Set Chamber Gradients
    Set Heating Gradient    2.5
    Set Cooling Gradient    2.0
    ${up}=    Get Heating Gradient
    ${down}=    Get Cooling Gradient
    Should Be Equal As Numbers    ${up}    2.5
    Should Be Equal As Numbers    ${down}    2.0
