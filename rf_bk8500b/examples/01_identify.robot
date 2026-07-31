*** Settings ***
Library         BK8500BLibrary
Suite Setup     Connect To Electronic Load    %{BK8500B_PORT}
Suite Teardown  Disconnect All Electronic Loads

*** Test Cases ***
Identify Load And Inspect Capabilities
    ${identity}=    Identify Electronic Load
    Log    ${identity}
    Should Not Be Empty    ${identity}[model]
    ${caps}=    Get Electronic Load Capabilities
    Should Be True    ${caps}[maximum_voltage_v] > 0
