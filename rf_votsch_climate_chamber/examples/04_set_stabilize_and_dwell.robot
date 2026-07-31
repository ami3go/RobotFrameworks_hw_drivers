*** Settings ***
Library         votsch_climate_chamber.robot_library.VotschClimateChamberLibrary
Suite Setup     Connect Climate Chamber    192.168.1.50    -40    180
Suite Teardown  Stop And Disconnect Climate Chamber

*** Test Cases ***
Run At 85 Degrees
    ${final}=    Set Temperature And Wait
    ...    target=85
    ...    tolerance=0.8
    ...    stable_samples=3
    ...    poll_interval=10 s
    ...    timeout=2 h
    ...    dwell=30 min
    Log    Final temperature: ${final} °C
