*** Settings ***
Library         votsch_climate_chamber.robot_library.VotschClimateChamberLibrary
Suite Setup     Connect Climate Chamber    192.168.1.50    -40    180
Suite Teardown  Stop And Disconnect Climate Chamber

*** Test Cases ***
Verify Operating Point
    Set Climate Chamber Temperature    25
    Start Climate Chamber
    Wait Until Climate Chamber Is Stable    25    tolerance=0.5    stable_samples=3
    Climate Chamber Temperature Should Be           25    tolerance=0.5
    Climate Chamber Temperature Should Be Within    24.5    25.5
    Climate Chamber Should Be Running
