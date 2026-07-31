*** Settings ***
Library         votsch_climate_chamber.robot_library.VotschClimateChamberLibrary
Suite Setup     Connect Climate Chamber    192.168.1.50    -40    180
Suite Teardown  Stop And Disconnect Climate Chamber

*** Test Cases ***
Teardown Still Runs After Test Failure
    Set Climate Chamber Temperature    25
    Start Climate Chamber
    Climate Chamber Should Be Running
    # A later DUT assertion may fail; Suite Teardown still stops the chamber.
