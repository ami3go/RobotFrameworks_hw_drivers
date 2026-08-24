*** Settings ***
Library    rf_keysight349xx.library.Keysight349xxLibrary
Suite Teardown    Disconnect All
*** Test Cases ***
Verify Empty Error Queue
    Connect    SIM::34972A    alias=daq
    Device Error Queue Should Be Empty    alias=daq
    ${errors}=    Get All Device Errors    alias=daq
    Should Be Empty    ${errors}
