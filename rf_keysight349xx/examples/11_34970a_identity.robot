*** Settings ***
Library    rf_keysight349xx.library.Keysight349xxLibrary
Suite Teardown    Disconnect All
*** Test Cases ***
Read 34970A Identity
    Connect    SIM::34970A    alias=daq
    ${idn}=    Get Identity    alias=daq
    Should Contain    ${idn}    34970A
