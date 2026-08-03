*** Settings ***
Library         rf_bk8500b.BK8500BLibrary
Suite Setup     Connect To Electronic Load    %{BK8500B_PORT}
Suite Teardown  Disconnect All Electronic Loads
Test Teardown   Disable Electronic Load Input

*** Test Cases ***
Constant Resistance Mode
    Configure And Enable Load    CR    100.0
    ${resistance}=    Measure Resistance
    Log    Measured resistance: ${resistance} ohm
