*** Settings ***
Library    rf_keysight349xx.library.Keysight349xxLibrary
Suite Teardown    Disconnect All
*** Test Cases ***
Read Slot 300
    Connect    SIM::34972A    alias=daq
    ${module}=    Get Module Information    300    alias=daq    refresh=True
    Should Be Equal    ${module}[model]    34907A
