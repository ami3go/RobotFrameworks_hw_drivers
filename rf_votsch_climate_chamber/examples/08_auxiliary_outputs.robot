*** Settings ***
Documentation    Model-dependent auxiliary outputs; simulator use only until mapping is qualified.
Library    rf_votsch_climate_chamber.VotschClimateChamberLibrary
Suite Setup    Connect    SIM::default
Suite Teardown    Run Keywords    Safe Shutdown    AND    Disconnect All

*** Test Cases ***
Exercise Simulator Auxiliary Outputs
    Set Dryer    ${TRUE}
    Should Be True    ${{ True }}
    ${dryer}=    Get Dryer
    Should Be True    ${dryer}
    Set Compressed Air    ${TRUE}
    ${air}=    Get Compressed Air
    Should Be True    ${air}
    Set Fan    ${TRUE}
    ${fan}=    Get Fan
    Should Be True    ${fan}
