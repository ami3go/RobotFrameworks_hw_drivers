*** Settings ***
Library         rf_bk8500b.BK8500BLibrary
Suite Setup     Connect To Electronic Load    %{BK8500B_PORT}
Suite Teardown  Disconnect All Electronic Loads
Test Teardown   Disable Electronic Load Input

*** Test Cases ***
Configure Continuous Transient Current
    Set Electronic Load Mode    Dynamic
    Configure Transient Load
    ...    high_level=1.0
    ...    high_dwell=0.5
    ...    low_level=0.1
    ...    low_dwell=0.5
    ...    slew_a_per_us=0.2
    ...    mode=continuous
    Enable Electronic Load Input
    Trigger Electronic Load
    ${config}=    Get Transient Load Configuration
    Should Be Equal As Numbers    ${config}[high_level]    1.0
