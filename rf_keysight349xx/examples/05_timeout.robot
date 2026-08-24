*** Settings ***
Library    rf_keysight349xx.library.Keysight349xxLibrary
Suite Teardown    Disconnect All
*** Test Cases ***
Configure Timeout
    ${value}=    Set Communication Timeout    2.0
    Should Be Equal As Numbers    ${value}    2.0
    Connect    SIM::34972A    alias=daq
    ${session_value}=    Set Communication Timeout    1.5    alias=daq
    Log    ${session_value}
