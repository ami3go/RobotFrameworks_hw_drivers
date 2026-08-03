*** Settings ***
Documentation    Open two simulated loads and switch between aliases explicitly.
Library          rf_bk8500_load.BK8500Library    auto_connect=${FALSE}
Suite Teardown   Close All Load Connections

*** Test Cases ***
Control Two Aliases
    Open Load Connection    simulated=${TRUE}    model=8500    alias=load_a
    Open Load Connection    simulated=${TRUE}    model=8502    alias=load_b
    ${b}=    Get Load Rated Limits
    Should Be Equal    ${b}[model]    8502
    Switch Load Connection    load_a
    ${a}=    Get Load Rated Limits
    Should Be Equal    ${a}[model]    8500
