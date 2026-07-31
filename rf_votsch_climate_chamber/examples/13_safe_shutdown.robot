*** Settings ***
Documentation    Demonstrates explicit safe shutdown using the simulator.
Library          rf_votsch_climate_chamber.library.VotschClimateChamberLibrary
Suite Setup      Connect    resource=SIM::safe-shutdown    alias=default
Suite Teardown   Disconnect All

*** Test Cases ***
Put Chamber Into Safe State
    Set Dryer    ${TRUE}
    Set Compressed Air    ${TRUE}
    Start Chamber
    ${result}=    Safe Shutdown
    Should Be True    ${result}[safe]
    Chamber Should Be Stopped
    Should Not Be True    ${result}[dryer]
    Should Not Be True    ${result}[compressed_air]
