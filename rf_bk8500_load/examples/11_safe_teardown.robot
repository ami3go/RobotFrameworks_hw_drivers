*** Settings ***
Documentation    Verify that the explicit safe-state sequence opens the input.
Resource         resources/bk8500_example.resource
Suite Setup      Prepare Example Load
Suite Teardown   Safe Example Teardown

*** Test Cases ***
Return To Safe State
    Apply Constant Current    ${0.5}    enable_input=${TRUE}
    Reset Load To Safe State
    Claim Remote Control
    Load Input State Should Be    OFF
