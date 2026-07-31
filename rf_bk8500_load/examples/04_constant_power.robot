*** Settings ***
Documentation    Apply a conservative constant-power load.
Resource         resources/bk8500_example.resource
Suite Setup      Prepare Example Load
Suite Teardown   Safe Example Teardown

*** Test Cases ***
Sink Twelve Watts
    Apply Constant Power    ${12.0}    enable_input=${TRUE}
    Wait Until Load Reading Is Stable    quantity=power    tolerance=${0.05}
    Load Power Should Be Within    ${12.0}    ${0.2}
