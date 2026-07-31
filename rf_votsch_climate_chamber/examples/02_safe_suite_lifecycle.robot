*** Settings ***
Library         votsch_climate_chamber.robot_library.VotschClimateChamberLibrary    stop_on_close=${TRUE}
Suite Setup     Connect Chamber For Suite
Suite Teardown  Stop And Disconnect Climate Chamber

*** Test Cases ***
Connection Is Healthy
    Climate Chamber Should Be Connected
    ${idn}=    Get Climate Chamber Identification
    Log    ${idn}

*** Keywords ***
Connect Chamber For Suite
    Connect Climate Chamber    192.168.1.50    -40    180    retries=3
