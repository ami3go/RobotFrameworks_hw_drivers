*** Settings ***
Library    rf_keysight349xx.library.Keysight349xxLibrary
Suite Teardown    Disconnect All

*** Test Cases ***
Simulator Smoke
    ${state}=    Connect    SIM::34972A    alias=daq
    Should Be True    ${state}[connected]
    ${idn}=    Get Identity    alias=daq
    Should Contain    ${idn}    34972A
    ${mods}=    Get Installed Modules    alias=daq
    Should Not Be Empty    ${mods}
