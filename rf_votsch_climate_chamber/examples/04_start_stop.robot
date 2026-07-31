*** Settings ***
Documentation    Explicit chamber operating-state control.
Library    rf_votsch_climate_chamber.library.VotschClimateChamberLibrary
Suite Setup    Connect    SIM::default
Suite Teardown    Run Keywords    Safe Shutdown    AND    Disconnect All

*** Test Cases ***
Start And Stop Chamber
    Start Chamber
    Chamber Should Be Running
    Stop Chamber
    Chamber Should Be Stopped
