*** Settings ***
Library         FakeBK8500BLibrary.py
Suite Setup     Connect To Electronic Load    FAKE
Suite Teardown  Disconnect All Electronic Loads

*** Test Cases ***
Identity And Measurement Keywords Work
    ${identity}=    Identify Electronic Load
    Should Be Equal    ${identity}[model]    BK8500B
    ${voltage}=    Measure Voltage
    Should Be Equal As Numbers    ${voltage}    12.0

Safe Constant Current Sequence Works
    ${result}=    Configure And Enable Load    CC    1.0    current_limit=1.2    power_limit=20
    Should Be True    ${result}[input_enabled]
    Current Should Be Within Range    0.9    1.1
    Disable Electronic Load Input
    Electronic Load Input Should Be Off

Structured Status And Diagnostics Work
    ${status}=    Get Electronic Load Status
    Should Be Equal    ${status}[operating_mode]    CURRent
    ${health}=    Run Electronic Load Health Check
    Should Be True    ${health}[healthy]

Alias Sessions Work
    Connect To Electronic Load    FAKE2    alias=second
    ${sessions}=    List Electronic Load Sessions
    Length Should Be    ${sessions}    2
    Switch Electronic Load    default
