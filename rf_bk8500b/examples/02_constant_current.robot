*** Settings ***
Library         rf_bk8500b.BK8500BLibrary
Suite Setup     Connect To Electronic Load    %{BK8500B_PORT}
Suite Teardown  Disconnect All Electronic Loads
Test Teardown   Disable Electronic Load Input

*** Test Cases ***
Constant Current Load At One Ampere
    ${result}=    Configure And Enable Load    CC    1.0    current_limit=1.2    power_limit=20
    Should Be True    ${result}[input_enabled]
    Current Should Be Within Range    0.95    1.05
    Voltage Should Be Within Range    10.0    15.0
