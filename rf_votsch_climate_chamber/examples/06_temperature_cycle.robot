*** Settings ***
Library         votsch_climate_chamber.robot_library.VotschClimateChamberLibrary
Suite Setup     Connect Climate Chamber    192.168.1.50    -40    180
Suite Teardown  Stop And Disconnect Climate Chamber

*** Test Cases ***
Cold Ambient Hot Cycle
    FOR    ${target}    IN    -20    25    85    25
        Set Temperature And Wait
        ...    ${target}
        ...    dwell=10 min
        ...    tolerance=1.0
        ...    stable_samples=3
        ...    timeout=3 h
    END
