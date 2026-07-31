*** Settings ***
Documentation    Structured diagnostics and evidence export.
Library    rf_votsch_climate_chamber.library.VotschClimateChamberLibrary
Library    Collections
Library    OperatingSystem
Suite Setup    Connect    SIM::default
Suite Teardown    Disconnect All

*** Test Cases ***
Export Driver Diagnostics
    Check Communication
    ${diagnostics}=    Get Diagnostics
    Log Dictionary    ${diagnostics}
    ${result}=    Export Diagnostics    ${OUTPUT DIR}${/}diagnostics.json
    File Should Exist    ${result}[path]
