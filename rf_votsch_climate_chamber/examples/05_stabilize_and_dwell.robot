*** Settings ***
Documentation    Bounded stabilization and dwell workflow.
Library    rf_votsch_climate_chamber.library.VotschClimateChamberLibrary
Suite Setup    Connect    SIM::default
Suite Teardown    Run Keywords    Safe Shutdown    AND    Disconnect All

*** Test Cases ***
Set Stabilize And Dwell
    ${final}=    Set Temperature And Wait
    ...    35
    ...    dwell_s=100 milliseconds
    ...    poll_interval_s=10 milliseconds
    ...    settle_timeout_s=2 seconds
    ...    stable_samples=1
    Should Be Equal As Numbers    ${final}    35
