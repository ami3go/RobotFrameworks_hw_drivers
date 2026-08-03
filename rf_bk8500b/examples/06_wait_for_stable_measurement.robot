*** Settings ***
Library         rf_bk8500b.BK8500BLibrary
Suite Setup     Connect To Electronic Load    %{BK8500B_PORT}
Suite Teardown  Disconnect All Electronic Loads
Test Teardown   Disable Electronic Load Input

*** Test Cases ***
Wait For Supply To Stabilize
    Configure And Enable Load    CC    0.5    current_limit=0.7
    ${voltage}=    Wait Until Measurement Is Within Range
    ...    voltage
    ...    11.8
    ...    12.2
    ...    timeout=15
    ...    interval=0.5
    Log    Stable voltage: ${voltage} V
