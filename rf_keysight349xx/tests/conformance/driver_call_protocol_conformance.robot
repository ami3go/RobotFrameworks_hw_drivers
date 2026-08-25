*** Settings ***
Library    rf_keysight349xx.library.Keysight349xxLibrary
Resource    resources/conformance_variables.resource
Resource    resources/conformance_keywords.resource
Suite Teardown    Disconnect All

*** Test Cases ***
Universal API And Initial Protocol Slice
    ${state}=    Connect Simulator
    Check Communication    alias=${ALIAS}
    ${idn}=    Get Identity    alias=${ALIAS}
    Should Contain    ${idn}    34972A
    ${ver}=    Get SCPI Version    alias=${ALIAS}
    Should Be Equal    ${ver}    1994.0
    Device Error Queue Should Be Empty    alias=${ALIAS}

Measurement API Protocol Slice
    Connect Simulator
    ${channels}=    List Channels    alias=${ALIAS}
    Should Contain    ${channels}    101
    ${valid}=    Validate Channel    101    alias=${ALIAS}
    Should Be True    ${valid}
    ${dcv}=    Measure DC Voltage    101    alias=${ALIAS}
    ${acv}=    Measure AC Voltage    102    range_value=10    resolution=0.001    alias=${ALIAS}
    ${dci}=    Measure DC Current    121    range_value=1    alias=${ALIAS}
    ${aci}=    Measure AC Current    122    alias=${ALIAS}
    ${res}=    Measure Resistance    103    alias=${ALIAS}
    ${fres}=    Measure 4 Wire Resistance    104    range_value=1000    resolution=1    alias=${ALIAS}
    ${freq}=    Measure Frequency    105    alias=${ALIAS}
    ${period}=    Measure Period    105    alias=${ALIAS}
    Should Be True    ${dcv} > 0
    Should Be True    ${acv} >= 0
    Should Be True    ${dci} > 0
    Should Be True    ${aci} > 0
    Should Be True    ${res} > 0
    Should Be True    ${fres} > 0
    Should Be True    ${freq} > 0
    Should Be True    ${period} > 0
