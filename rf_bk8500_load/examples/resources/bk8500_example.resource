*** Settings ***
Library    BK8500Library    auto_connect=${FALSE}
Library    Collections

*** Variables ***
${SIMULATED}          ${TRUE}
${PORT}               COM4
${BAUDRATE}           9600
${AUTO_DETECT_BAUDRATE}    ${FALSE}
${BAUDRATE_CANDIDATES}     4800,9600,19200,38400
${PROBE_TIMEOUT}           0.75
${MODEL}              8500
${MAX_VOLTAGE}        20.0
${MAX_CURRENT}        5.0
${MAX_POWER}          100.0

*** Keywords ***
Open Example Load
    Open Load Connection    port=${PORT}    baudrate=${BAUDRATE}    model=${MODEL}
    ...    simulated=${SIMULATED}    alias=example
    ...    auto_detect_baudrate=${AUTO_DETECT_BAUDRATE}
    ...    baudrate_candidates=${BAUDRATE_CANDIDATES}    probe_timeout=${PROBE_TIMEOUT}

Prepare Example Load
    Open Example Load
    Claim Remote Control
    Configure Load Protection    max_voltage=${MAX_VOLTAGE}
    ...    max_current=${MAX_CURRENT}    max_power=${MAX_POWER}

Safe Example Teardown
    Run Keyword And Ignore Error    Reset Load To Safe State
    Close All Load Connections
