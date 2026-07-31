*** Settings ***
Documentation    Demonstrate measurement and pass/fail oracle keywords.
Resource         resources/bk8500_example.resource
Suite Setup      Prepare Example Load
Suite Teardown   Safe Example Teardown

*** Test Cases ***
Verify Voltage Current And Power
    Apply Constant Current    ${1.0}    enable_input=${TRUE}
    ${reading}=    Measure Load Input
    Load Voltage Should Be Within    ${reading}[voltage_v]    ${0.001}
    Load Current Should Be Within    ${reading}[current_a]    ${0.001}
    Load Power Should Be Within      ${reading}[power_w]      ${0.001}
    Load Input State Should Be    ON
