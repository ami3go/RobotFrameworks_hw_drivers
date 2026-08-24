*** Settings ***
Library    rf_keysight349xx.library.Keysight349xxLibrary
Suite Teardown    Disconnect All
*** Test Cases ***
Read SCPI Version
    Connect    SIM::34972A    alias=daq
    ${version}=    Get SCPI Version    alias=daq
    Should Be Equal    ${version}    1994.0
