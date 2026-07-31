*** Settings ***
Library         BK8500BLibrary
Suite Setup     Connect To Electronic Load    %{BK8500B_PORT}
Suite Teardown  Disconnect All Electronic Loads
Test Teardown   Disable Electronic Load Input

*** Test Cases ***
Constant Power Mode
    Configure And Enable Load    CP    10.0    current_limit=2.0    power_limit=15.0
    Power Should Be Within Range    9.5    10.5
