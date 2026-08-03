*** Settings ***
Documentation     Hardware smoke test. The first test is non-destructive; disconnect applies the configured safe-shutdown policy.
Library           rf_votsch_climate_chamber.VotschClimateChamberLibrary
Library           Collections
Suite Setup       Configure Read Only Disconnect And Connect
Suite Teardown    Disconnect    alias=default
Force Tags        hardware    climate_chamber

*** Variables ***
${CHAMBER_IP}              192.168.0.11
${CHAMBER_PORT}            2049
${TEMP_MIN}                -40
${TEMP_MAX}                180
${SAFE_TARGET}             15
${ALLOW_CHAMBER_CONTROL}   ${TRUE}
${SETPOINT_VERIFY_TIMEOUT_S}    30.0

*** Test Cases ***
Read Only Communication Smoke Test
    Connection Should Be Available
    ${identity}=    Get Identity
    ${state}=       Get Connection State    refresh=${TRUE}
    ${diagnostics}=    Get Diagnostics
    Log    ${identity}
    Log Dictionary    ${state}
    Log Dictionary    ${diagnostics}

Opt In Setpoint Readback Test
    Skip If    not ${ALLOW_CHAMBER_CONTROL}    Pass --variable ALLOW_CHAMBER_CONTROL:True after operator approval.
    ${original}=    Get Temperature Setpoint
    TRY
        Set Temperature    ${SAFE_TARGET}
        Temperature Setpoint Should Be    ${SAFE_TARGET}
    FINALLY
        Set Temperature    ${original}
    END

*** Keywords ***
Configure Read Only Disconnect And Connect
    ${configuration}=    Get Driver Configuration
    Set To Dictionary    ${configuration}[settings][safety]    safe_shutdown_on_disconnect=${FALSE}
    ${result}=    Import Driver Configuration    ${configuration}    apply=${TRUE}
    Should Be True    ${result}[valid]
    Should Be True    ${result}[applied]
    Connect To Hardware Chamber

Connect To Hardware Chamber
    ${resource}=    Set Variable    tcp://${CHAMBER_IP}:${CHAMBER_PORT}
    Connect
    ...    resource=${resource}
    ...    alias=default
    ...    timeout_s=5 s
    ...    temperature_min_c=${TEMP_MIN}
    ...    temperature_max_c=${TEMP_MAX}
    ...    setpoint_verify_timeout_s=${SETPOINT_VERIFY_TIMEOUT_S}
