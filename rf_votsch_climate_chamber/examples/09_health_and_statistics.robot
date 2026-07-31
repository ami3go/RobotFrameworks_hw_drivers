*** Settings ***
Library         votsch_climate_chamber.robot_library.VotschClimateChamberLibrary
Library         Collections
Suite Setup     Connect Climate Chamber    192.168.1.50    -40    180
Suite Teardown  Disconnect Climate Chamber

*** Test Cases ***
Capture Diagnostic Snapshot
    ${health}=    Get Climate Chamber Health
    ${stats}=     Get Climate Chamber Connection Statistics
    Log Dictionary    ${health}
    Log Dictionary    ${stats}
