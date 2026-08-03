*** Settings ***
Documentation    Named multi-session example.
Library    rf_votsch_climate_chamber.VotschClimateChamberLibrary
Suite Teardown    Disconnect All

*** Test Cases ***
Control Two Simulator Sessions
    Connect    SIM::one    alias=one
    Connect    SIM::two    alias=two
    Select Connection    one
    Set Temperature    30
    Select Connection    two
    Set Temperature    40
    ${connections}=    List Connections
    Length Should Be    ${connections}    2
