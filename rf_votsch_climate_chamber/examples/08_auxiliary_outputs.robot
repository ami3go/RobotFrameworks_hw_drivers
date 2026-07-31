*** Settings ***
Library         votsch_climate_chamber.robot_library.VotschClimateChamberLibrary
Suite Setup     Connect Climate Chamber    192.168.1.50    -40    180
Suite Teardown  Disable Outputs And Disconnect

*** Test Cases ***
Enable Dryer And Compressed Air
    ${dryer}=    Set Climate Chamber Dryer            ON
    ${air}=       Set Climate Chamber Compressed Air   ON
    Should Be True    ${dryer}
    Should Be True    ${air}

*** Keywords ***
Disable Outputs And Disconnect
    Run Keyword And Ignore Error    Set Climate Chamber Dryer           OFF
    Run Keyword And Ignore Error    Set Climate Chamber Compressed Air  OFF
    Disconnect Climate Chamber
