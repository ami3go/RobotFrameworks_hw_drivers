*** Settings ***
Library         BK8500BLibrary
Suite Setup     Connect To Electronic Load    %{BK8500B_PORT}
Suite Teardown  Disconnect All Electronic Loads
Test Teardown   Disable Electronic Load Input

*** Test Cases ***
Constant Voltage Mode
    Configure And Enable Load    CV    5.0    current_limit=2.0    power_limit=20
    ${setpoint}=    Get Voltage Setpoint
    Should Be Equal As Numbers    ${setpoint}    5.0
    ${snapshot}=    Get Measurement Snapshot
    Log    ${snapshot}
