*** Settings ***
Documentation    Configure a 1 A constant-current sink and verify the simulator reading.
Resource         resources/bk8500_example.resource
Suite Setup      Prepare Example Load
Suite Teardown   Safe Example Teardown

*** Test Cases ***
Sink One Ampere
    Apply Constant Current    ${1.0}    enable_input=${TRUE}
    Wait Until Load Reading Is Stable    quantity=current    tolerance=${0.01}
    Load Current Should Be Within    ${1.0}    ${0.02}
    Load Should Report No Protection Faults
