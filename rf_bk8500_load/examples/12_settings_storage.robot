*** Settings ***
Documentation    Save and recall a conservative configuration register.
Resource         resources/bk8500_example.resource
Suite Setup      Prepare Example Load
Suite Teardown   Safe Example Teardown

*** Test Cases ***
Save And Recall Register One
    Apply Constant Current    ${0.75}
    Save Load Settings    1
    Apply Constant Current    ${0.25}
    Recall Load Settings    1
    ${value}=    Get Load Setpoint    CC
    Should Be Equal As Numbers    ${value}    ${0.75}    precision=4
