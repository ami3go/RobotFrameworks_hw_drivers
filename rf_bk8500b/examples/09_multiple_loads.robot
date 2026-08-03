*** Settings ***
Library         rf_bk8500b.BK8500BLibrary
Suite Teardown  Disconnect All Electronic Loads

*** Test Cases ***
Use Two Loads By Alias
    Connect To Electronic Load    %{BK8500B_PORT_A}    alias=load_a
    Connect To Electronic Load    %{BK8500B_PORT_B}    alias=load_b
    ${voltage_a}=    Measure Voltage    alias=load_a
    ${voltage_b}=    Measure Voltage    alias=load_b
    Log Many    ${voltage_a}    ${voltage_b}
    ${sessions}=    List Electronic Load Sessions
    Length Should Be    ${sessions}    2
