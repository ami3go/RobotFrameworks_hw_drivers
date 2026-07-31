*** Settings ***
Library         votsch_climate_chamber.robot_library.VotschClimateChamberLibrary
Variables       variables_example.py
Suite Setup     Connect From Configuration
Suite Teardown  Stop And Disconnect Climate Chamber

*** Test Cases ***
Configured Ambient Test
    Set Temperature And Wait
    ...    ${ambient_target}
    ...    tolerance=${stability_tolerance}
    ...    timeout=${stability_timeout}

*** Keywords ***
Connect From Configuration
    Connect Climate Chamber
    ...    ${chamber_ip}
    ...    ${temperature_min}
    ...    ${temperature_max}
    ...    port=${chamber_port}
