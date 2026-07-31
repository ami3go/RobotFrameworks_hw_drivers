*** Settings ***
Library         votsch_climate_chamber.robot_library.VotschClimateChamberLibrary
Library         Collections
Suite Setup     Connect Climate Chamber    192.168.1.50    -20    120
Suite Teardown  Disconnect Climate Chamber

*** Test Cases ***
Use Restricted DUT Limits
    ${limits}=    Get Climate Chamber Temperature Limits
    Log Dictionary    ${limits}
    Set Climate Chamber Temperature Limits    -10    85
    Set Climate Chamber Temperature    85
