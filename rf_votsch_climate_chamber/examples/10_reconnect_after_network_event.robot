*** Settings ***
Library         votsch_climate_chamber.robot_library.VotschClimateChamberLibrary
Suite Setup     Connect Climate Chamber    192.168.1.50    -40    180    retries=3
Suite Teardown  Disconnect Climate Chamber

*** Test Cases ***
Explicitly Reconnect And Continue
    Reconnect Climate Chamber
    Climate Chamber Should Be Connected
    ${temperature}=    Get Climate Chamber Temperature
    Log    Temperature after reconnect: ${temperature} °C
