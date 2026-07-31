*** Settings ***
Library         votsch_climate_chamber.robot_library.VotschClimateChamberLibrary
Suite Setup     Connect Climate Chamber    192.168.1.50    -40    180
Suite Teardown  Disconnect Climate Chamber

*** Test Cases ***
Configure Safe Gradients
    ${up}=      Set Climate Chamber Heating Gradient    2.0
    ${down}=    Set Climate Chamber Cooling Gradient    1.5
    Should Be Equal As Numbers    ${up}      2.0
    Should Be Equal As Numbers    ${down}    1.5
