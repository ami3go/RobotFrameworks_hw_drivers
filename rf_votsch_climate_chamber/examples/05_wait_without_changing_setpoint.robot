*** Settings ***
Library         votsch_climate_chamber.robot_library.VotschClimateChamberLibrary
Suite Setup     Connect Climate Chamber    192.168.1.50    -40    180
Suite Teardown  Disconnect Climate Chamber

*** Test Cases ***
Observe Existing Chamber Program
    ${setpoint}=    Get Climate Chamber Setpoint
    ${final}=    Wait Until Climate Chamber Is Stable
    ...    target=${setpoint}
    ...    tolerance=0.5
    ...    stable_samples=5
    ...    timeout=4 h
    Log    Stable at ${final} °C
