*** Settings ***
Documentation     Real-chamber verification of the canonical API 3.0 keyword surface. State-changing tests require explicit authorization.
Library           rf_votsch_climate_chamber.VotschClimateChamberLibrary    managed_configuration_root=${OUTPUT DIR}${/}profiles
Library           Collections
Library           OperatingSystem
Suite Setup       Connect And Capture Original Chamber State
Suite Teardown    Restore Original Chamber State And Disconnect
Test Setup        Connection Should Be Available
Force Tags        hardware    climate_chamber    api-verification    rfds-019-hil

*** Variables ***
${CHAMBER_IP}                   REQUIRED
${CHAMBER_PORT}                 2049
${TEMPERATURE_MIN}              -40
${TEMPERATURE_MAX}              180
${SAFE_TEST_TEMPERATURE}        25
${STABILITY_TOLERANCE}          1.0
${STABILITY_TIMEOUT}            30 min
${STABLE_SAMPLES}               3
${POLL_INTERVAL}                10 s
${DWELL_DURATION}               1 s
${TEST_HEATING_GRADIENT}        1.0
${TEST_COOLING_GRADIENT}        1.0
${ALLOW_CHAMBER_CONTROL}        ${FALSE}
${ALLOW_AUXILIARY_OUTPUTS}      ${FALSE}
${DRYER_OUTPUT_CHANNEL}          ${NONE}
${COMPRESSED_AIR_OUTPUT_CHANNEL}    ${NONE}
${SETPOINT_VERIFY_TIMEOUT_S}     30.0

*** Test Cases ***
01 Verify Metadata And Capability API
    ${info}=    Get Driver Information
    ${capabilities}=    Get Driver Capabilities
    ${model}=    Get Capability Model
    Should Be Equal    ${info}[api_version]    3.0.0
    Should Not Be Empty    ${capabilities}
    Should Not Be Empty    ${model}
    Log Dictionary    ${info}
    Log List    ${capabilities}

02 Verify Identity Diagnostics And Read API
    ${identity}=    Get Identity    refresh=${TRUE}
    ${status}=      Get Chamber Status
    ${setpoint}=    Get Temperature Setpoint
    ${temperature}=    Measure Temperature
    ${limits}=      Get Temperature Limits
    ${heat_gradient}=    Get Heating Gradient
    ${cool_gradient}=    Get Cooling Gradient
    ${running}=     Get Chamber Running State
    IF    ${ALLOW_AUXILIARY_OUTPUTS}
        ${dryer}=       Get Dryer
        ${air}=         Get Compressed Air
    ELSE
        ${dryer}=       Set Variable    NOT CONFIGURED
        ${air}=         Set Variable    NOT CONFIGURED
    END
    ${diagnostics}=    Get Diagnostics
    ${export}=      Export Diagnostics    ${OUTPUT DIR}${/}hardware_diagnostics.json
    Should Not Be Empty    ${identity}
    Should Not Be Empty    ${status}
    Should Be True    isinstance($setpoint, (int, float))
    Should Be True    isinstance($temperature, (int, float))
    File Should Exist    ${export}[path]
    Log Many    ${limits}    ${heat_gradient}    ${cool_gradient}    ${dryer}    ${air}    ${running}
    Log Dictionary    ${diagnostics}

03 Verify Connection And Session API
    # "Should Be True    Is Connected" evaluates the literal string as a Python
    # expression rather than calling the keyword — assign the result first.
    ${connected}=    Is Connected
    Should Be True    ${connected}
    ${state}=    Get Connection State    refresh=${TRUE}
    Should Be True    ${state}[connected]
    ${communication_ok}=    Check Communication
    Should Be True    ${communication_ok}
    ${connections}=    List Connections
    Should Not Be Empty    ${connections}
    ${selected}=    Select Connection    default
    Should Be Equal    ${selected}[alias]    default
    ${active}=    Get Active Connection
    Should Be Equal    ${active}    default
    ${original_timeout}=    Get Communication Timeout
    ${applied}=    Set Communication Timeout    3 s
    Should Be Equal As Numbers    ${applied}    3
    Set Communication Timeout    ${original_timeout}
    ${reconnected}=    Reconnect
    Should Be True    ${reconnected}[connected]

04 Verify Configuration API
    ${schema}=    Get Driver Configuration Schema
    ${defaults}=    Get Driver Default Configuration
    ${effective}=    Get Driver Configuration
    ${validation}=    Validate Driver Configuration    ${effective}
    Should Be True    ${validation}[valid]
    ${imported}=    Import Driver Configuration    ${effective}
    ${exported}=    Export Driver Configuration    ${OUTPUT DIR}${/}driver_configuration.json    overwrite=${TRUE}
    File Should Exist    ${exported}[destination]
    ${saved}=    Save Driver Configuration    hardware_api_profile    overwrite=${TRUE}
    ${profiles}=    List Driver Configuration Profiles
    Should Not Be Empty    ${profiles}
    ${loaded}=    Load Driver Configuration    hardware_api_profile
    ${deleted}=    Delete Driver Configuration Profile    hardware_api_profile    confirm=${TRUE}
    ${reset}=    Reset Driver Configuration
    Log Many    ${schema}    ${defaults}    ${imported}    ${saved}    ${loaded}    ${deleted}    ${reset}

05 Verify Local Limits And Assertions
    ${original_limits}=    Get Temperature Limits
    TRY
        ${limits}=    Set Temperature Limits    ${TEMPERATURE_MIN}    ${TEMPERATURE_MAX}
        Should Be Equal As Numbers    ${limits}[min]    ${TEMPERATURE_MIN}
        Should Be Equal As Numbers    ${limits}[max]    ${TEMPERATURE_MAX}
        ${setpoint}=    Get Temperature Setpoint
        ${temperature}=    Measure Temperature
        Temperature Setpoint Should Be    ${setpoint}    tolerance_c=0.1
        Temperature Should Be    ${temperature}    tolerance_c=0.1
        ${low}=     Evaluate    float($temperature) - 0.1
        ${high}=    Evaluate    float($temperature) + 0.1
        Temperature Should Be Within    ${low}    ${high}
        ${running}=    Get Chamber Running State
        IF    ${running}
            Chamber Should Be Running
        ELSE
            Chamber Should Be Stopped
        END
    FINALLY
        Set Temperature Limits    ${original_limits}[min]    ${original_limits}[max]
    END

06 Verify Zero Duration Wait API
    ${temperature}=    Wait For Dwell    0 s    poll_interval_s=1 s
    Should Be True    isinstance($temperature, (int, float))

07 Verify Setpoint Start Stop And Stability API
    Skip If    not ${ALLOW_CHAMBER_CONTROL}    Enable with --variable ALLOW_CHAMBER_CONTROL:True after operator approval.
    Set Temperature    ${SAFE_TEST_TEMPERATURE}
    Temperature Setpoint Should Be    ${SAFE_TEST_TEMPERATURE}    tolerance_c=0.1
    Start Chamber
    Chamber Should Be Running
    ${stable}=    Wait For Temperature Stability
    ...    target_c=${SAFE_TEST_TEMPERATURE}
    ...    tolerance_c=${STABILITY_TOLERANCE}
    ...    stable_samples=${STABLE_SAMPLES}
    ...    poll_interval_s=${POLL_INTERVAL}
    ...    settle_timeout_s=${STABILITY_TIMEOUT}
    ${final}=    Set Temperature And Wait
    ...    value_c=${SAFE_TEST_TEMPERATURE}
    ...    dwell_s=${DWELL_DURATION}
    ...    tolerance_c=${STABILITY_TOLERANCE}
    ...    poll_interval_s=${POLL_INTERVAL}
    ...    settle_timeout_s=${STABILITY_TIMEOUT}
    ...    stable_samples=${STABLE_SAMPLES}
    ...    start_chamber=${TRUE}
    Should Be True    abs($stable - float($SAFE_TEST_TEMPERATURE)) <= float($STABILITY_TOLERANCE)
    Should Be True    abs($final - float($SAFE_TEST_TEMPERATURE)) <= float($STABILITY_TOLERANCE)
    Stop Chamber
    Chamber Should Be Stopped

08 Verify Gradient API
    Skip If    not ${ALLOW_CHAMBER_CONTROL}    Enable with --variable ALLOW_CHAMBER_CONTROL:True after operator approval.
    Set Heating Gradient    ${TEST_HEATING_GRADIENT}
    Set Cooling Gradient    ${TEST_COOLING_GRADIENT}
    ${heating}=    Get Heating Gradient
    ${cooling}=    Get Cooling Gradient
    Should Be Equal As Numbers    ${heating}    ${TEST_HEATING_GRADIENT}
    Should Be Equal As Numbers    ${cooling}    ${TEST_COOLING_GRADIENT}

09 Verify Auxiliary Output API
    Skip If    not ${ALLOW_AUXILIARY_OUTPUTS}    Enable only after hardware output mapping is confirmed.
    Set Dryer    ${TRUE}
    Set Compressed Air    ${TRUE}
    ${dryer}=    Get Dryer
    ${air}=    Get Compressed Air
    Should Be True    ${dryer}
    Should Be True    ${air}
    Set Dryer    ${FALSE}
    Set Compressed Air    ${FALSE}
    ${dryer}=    Get Dryer
    ${air}=    Get Compressed Air
    Should Not Be True    ${dryer}
    Should Not Be True    ${air}

10 Verify Cancellation And Safe Shutdown API
    Skip If    not ${ALLOW_CHAMBER_CONTROL}    Safe shutdown changes physical chamber state and requires operator approval.
    Cancel Current Operation
    Reconnect
    ${result}=    Safe Shutdown
    Should Be True    ${result}[safe]
    Chamber Should Be Stopped

11 Verify Disconnect And Reconnect API
    Disconnect    alias=default
    ${connected}=    Is Connected    alias=default
    Should Not Be True    ${connected}
    Connect To Hardware Chamber
    Connection Should Be Available

*** Keywords ***
Connect To Hardware Chamber
    ${resource}=    Set Variable    tcp://${CHAMBER_IP}:${CHAMBER_PORT}
    ${state}=    Connect
    ...    resource=${resource}
    ...    alias=default
    ...    timeout_s=5 s
    ...    temperature_min_c=${TEMPERATURE_MIN}
    ...    temperature_max_c=${TEMPERATURE_MAX}
    ...    setpoint_verify_timeout_s=${SETPOINT_VERIFY_TIMEOUT_S}
    ...    dryer_output_channel=${DRYER_OUTPUT_CHANNEL}
    ...    compressed_air_output_channel=${COMPRESSED_AIR_OUTPUT_CHANNEL}
    RETURN    ${state}

Connect And Capture Original Chamber State
    ${configuration}=    Get Driver Configuration
    Set To Dictionary    ${configuration}[settings][safety]    safe_shutdown_on_disconnect=${FALSE}
    ${configuration_result}=    Import Driver Configuration    ${configuration}    apply=${TRUE}
    Should Be True    ${configuration_result}[valid]
    Should Be True    ${configuration_result}[applied]
    Should Not Be Equal    ${CHAMBER_IP}    REQUIRED    Set CHAMBER_IP on the Robot command line.
    ${state}=    Connect To Hardware Chamber
    Set Suite Variable    ${ORIGINAL_IDENTITY}    ${state}[identity]
    ${setpoint}=    Get Temperature Setpoint
    ${heating}=     Get Heating Gradient
    ${cooling}=     Get Cooling Gradient
    ${running}=     Get Chamber Running State
    IF    ${ALLOW_AUXILIARY_OUTPUTS}
        ${dryer}=       Get Dryer
        ${air}=         Get Compressed Air
    ELSE
        ${dryer}=       Set Variable    ${NONE}
        ${air}=         Set Variable    ${NONE}
    END
    Set Suite Variable    ${ORIGINAL_SETPOINT}    ${setpoint}
    Set Suite Variable    ${ORIGINAL_HEATING_GRADIENT}    ${heating}
    Set Suite Variable    ${ORIGINAL_COOLING_GRADIENT}    ${cooling}
    Set Suite Variable    ${ORIGINAL_DRYER}    ${dryer}
    Set Suite Variable    ${ORIGINAL_COMPRESSED_AIR}    ${air}
    Set Suite Variable    ${ORIGINAL_RUNNING}    ${running}

Restore Original Chamber State And Disconnect
    # Suite Setup may have failed before it reached its "Set Suite Variable"
    # calls (e.g. Get Dryer failing because ALLOW_AUXILIARY_OUTPUTS is TRUE but
    # DRYER_OUTPUT_CHANNEL was never set) — read each ORIGINAL_* value defensively
    # so a partial setup doesn't crash teardown with an unrelated "variable not
    # found" error and skip the unconditional Disconnect below.
    ${original_setpoint}=    Get Variable Value    $ORIGINAL_SETPOINT    ${NONE}
    ${original_heating}=    Get Variable Value    $ORIGINAL_HEATING_GRADIENT    ${NONE}
    ${original_cooling}=    Get Variable Value    $ORIGINAL_COOLING_GRADIENT    ${NONE}
    ${original_dryer}=    Get Variable Value    $ORIGINAL_DRYER    ${NONE}
    ${original_air}=    Get Variable Value    $ORIGINAL_COMPRESSED_AIR    ${NONE}
    ${original_running}=    Get Variable Value    $ORIGINAL_RUNNING    ${NONE}
    IF    $ALLOW_CHAMBER_CONTROL and $original_setpoint is not None
        Run Keyword And Ignore Error    Set Heating Gradient    ${original_heating}
        Run Keyword And Ignore Error    Set Cooling Gradient    ${original_cooling}
        Run Keyword And Ignore Error    Set Temperature    ${original_setpoint}
        IF    $ALLOW_AUXILIARY_OUTPUTS and $original_dryer is not None
            Run Keyword And Ignore Error    Set Dryer    ${original_dryer}
            Run Keyword And Ignore Error    Set Compressed Air    ${original_air}
        END
        IF    $original_running is not None
            IF    ${original_running}
                Run Keyword And Ignore Error    Start Chamber
            ELSE
                Run Keyword And Ignore Error    Stop Chamber
            END
        END
    END
    Run Keyword And Ignore Error    Disconnect    alias=default
