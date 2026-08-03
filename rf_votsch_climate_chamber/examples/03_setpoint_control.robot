*** Settings ***
Documentation    Configure and verify a safe temperature setpoint.
Library    rf_votsch_climate_chamber.VotschClimateChamberLibrary
Suite Setup    Connect    SIM::default
Suite Teardown    Run Keywords    Safe Shutdown    AND    Disconnect All

*** Test Cases ***
Set And Verify Temperature
    Set Temperature    30
    ${setpoint}=    Get Temperature Setpoint
    Should Be Equal As Numbers    ${setpoint}    30
    Temperature Setpoint Should Be    30    tolerance_c=0.05
