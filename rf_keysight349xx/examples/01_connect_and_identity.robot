*** Settings ***
Library    rf_keysight349xx.library.Keysight349xxLibrary
Suite Teardown    Disconnect All
*** Test Cases ***
Connect And Read Identity
    ${state}=    Connect    SIM::34972A    alias=daq
    Log    ${state}
    ${idn}=    Get Identity    alias=daq
    Log    ${idn}
