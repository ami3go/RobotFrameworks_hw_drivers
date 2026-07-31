*** Settings ***
Documentation    Apply a 12 ohm electronic resistance and inspect measurements.
Resource         resources/bk8500_example.resource
Suite Setup      Prepare Example Load
Suite Teardown   Safe Example Teardown

*** Test Cases ***
Apply Twelve Ohms
    Apply Constant Resistance    ${12.0}    enable_input=${TRUE}
    ${reading}=    Wait Until Load Reading Is Stable    quantity=current
    Log Dictionary    ${reading}
    Load Mode Should Be    CR
