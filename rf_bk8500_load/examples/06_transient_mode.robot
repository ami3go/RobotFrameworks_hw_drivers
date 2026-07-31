*** Settings ***
Documentation    Program a two-level current transient and verify the stored parameters.
Resource         resources/bk8500_example.resource
Suite Setup      Prepare Example Load
Suite Teardown   Safe Example Teardown

*** Test Cases ***
Configure Current Pulse
    Configure Load Transient    CC    ${0.5}    ${0.1}    ${1.0}    ${0.2}    operation=PULSE
    Set Load Function    TRANSIENT
    ${settings}=    Get Load Transient    CC
    Should Be Equal    ${settings}[operation]    PULSE
