*** Settings ***
Documentation    Select constant-voltage regulation and verify mode/setpoint readback.
Resource         resources/bk8500_example.resource
Suite Setup      Prepare Example Load
Suite Teardown   Safe Example Teardown

*** Test Cases ***
Configure Constant Voltage
    Apply Constant Voltage    ${6.0}
    Load Mode Should Be    CV
    ${setpoint}=    Get Load Setpoint    CV
    Should Be Equal As Numbers    ${setpoint}    ${6.0}    precision=3
