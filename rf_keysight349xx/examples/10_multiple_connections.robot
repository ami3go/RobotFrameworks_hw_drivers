*** Settings ***
Library    rf_keysight349xx.library.Keysight349xxLibrary
Suite Teardown    Disconnect All
*** Test Cases ***
Use Two Simulator Sessions
    Connect    SIM::34970A    alias=old
    Connect    SIM::34972A    alias=new
    ${items}=    List Connections
    Length Should Be    ${items}    2
    ${active}=    Select Connection    new
    Should Contain    ${active}[identity]    34972A
