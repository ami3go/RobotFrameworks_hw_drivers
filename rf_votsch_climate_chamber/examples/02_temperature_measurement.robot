*** Settings ***
Documentation    Read-only temperature measurement example.
Library    rf_votsch_climate_chamber.library.VotschClimateChamberLibrary
Suite Setup    Connect    SIM::default
Suite Teardown    Disconnect All

*** Test Cases ***
Measure Chamber Temperature
    ${temperature}=    Measure Temperature
    Log    Measured ${temperature} °C
    Temperature Should Be Within    -40    180
