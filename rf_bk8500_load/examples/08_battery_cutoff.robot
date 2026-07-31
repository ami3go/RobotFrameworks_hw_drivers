*** Settings ***
Documentation    Configure battery-test cut-off and LOAD ON timer without starting a discharge.
Resource         resources/bk8500_example.resource
Suite Setup      Prepare Example Load
Suite Teardown   Safe Example Teardown

*** Test Cases ***
Configure Battery Safeguards
    Set Battery Cutoff Voltage    ${9.0}
    Set Load On Timer    ${30}    enabled=${TRUE}
    Set Load Function    BATTERY
    ${timer}=    Get Load On Timer
    Should Be Equal As Integers    ${timer}[seconds]    30
