*** Settings ***
Documentation     Opt-in smoke test. Control-changing steps require ALLOW_CHAMBER_CONTROL=True.
Library           votsch_climate_chamber.robot_library.VotschClimateChamberLibrary
Suite Setup       Connect Climate Chamber    ${CHAMBER_IP}    ${TEMP_MIN}    ${TEMP_MAX}    port=${CHAMBER_PORT}
Suite Teardown    Disconnect Climate Chamber
Force Tags        hardware    climate_chamber

*** Variables ***
${CHAMBER_IP}              192.168.1.50
${CHAMBER_PORT}            2049
${TEMP_MIN}                -40
${TEMP_MAX}                180
${SAFE_TARGET}             25
${ALLOW_CHAMBER_CONTROL}   ${FALSE}

*** Test Cases ***
Read Only Communication Smoke Test
    Climate Chamber Should Be Connected
    ${health}=    Get Climate Chamber Health
    Log Dictionary    ${health}

Opt In Setpoint Readback Test
    Skip If    not ${ALLOW_CHAMBER_CONTROL}    Pass --variable ALLOW_CHAMBER_CONTROL:True after operator approval.
    ${original}=    Get Climate Chamber Setpoint
    TRY
        Set Climate Chamber Temperature    ${SAFE_TARGET}
        Climate Chamber Setpoint Should Be    ${SAFE_TARGET}
    FINALLY
        Set Climate Chamber Temperature    ${original}
    END
