*** Settings ***
Library         votsch_climate_chamber.robot_library.VotschClimateChamberLibrary
Suite Setup     Connect Climate Chamber    192.168.1.50    -40    180
Suite Teardown  Stop And Disconnect Climate Chamber

*** Test Cases ***
Read And Set Temperature
    ${actual}=    Get Climate Chamber Temperature
    Log    Initial temperature: ${actual} °C
    Set Climate Chamber Temperature    25
    Climate Chamber Setpoint Should Be    25
