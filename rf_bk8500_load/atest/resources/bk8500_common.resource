*** Settings ***
Documentation     Shared setup, teardown and helper keywords for BK8500 suites.
...               Run against hardware with:
...               robot --variable SIMULATED:False --variable PORT:/dev/ttyUSB0 atest
Library           BK8500Library    auto_connect=${FALSE}


*** Variables ***
${SIMULATED}          ${TRUE}
${PORT}               /dev/ttyUSB0
${BAUDRATE}           ${9600}
${MODEL}              8500
${ADDRESS}            ${0}
${MAX_VOLTAGE}        ${20}
${MAX_CURRENT}        ${5}
${MAX_POWER}          ${100}
# Expected source under test: 12 V bench supply, 50 mOhm of wiring.
${SOURCE_VOLTAGE}     ${12.0}
${SOURCE_RESISTANCE}  ${0.05}


*** Keywords ***
Connect To DC Load
    [Documentation]    Setup contract: open the port, claim remote control and
    ...                write the protection limits before any current flows.
    Open Load Connection    port=${PORT}    baudrate=${BAUDRATE}    model=${MODEL}
    ...    address=${ADDRESS}    simulated=${SIMULATED}
    ...    source_voltage=${SOURCE_VOLTAGE}    source_resistance=${SOURCE_RESISTANCE}
    ${info}=    Get Load Product Information
    Log    Connected to ${info}[model] (serial ${info}[serial_number], firmware ${info}[firmware_version])
    Claim Remote Control
    Configure Load Protection    max_voltage=${MAX_VOLTAGE}    max_current=${MAX_CURRENT}
    ...    max_power=${MAX_POWER}
    Load Input Off

Disconnect From DC Load
    [Documentation]    Suite teardown contract: input off, FIXED, panel released.
    Run Keyword And Ignore Error    Reset Load To Safe State
    Close All Load Connections

Return Load To Idle
    [Documentation]    Test teardown contract. Always leaves the input open.
    Load Input Off
    Set Load Function    FIXED

Sink And Settle
    [Documentation]    Apply a CC load and wait for the current to settle.
    [Arguments]    ${current}    ${tolerance}=${0.02}
    Apply Constant Current    ${current}    enable_input=${TRUE}
    Wait Until Load Reading Is Stable    quantity=current    tolerance=${tolerance}
    ...    window=${0.2}    timeout=${5}    interval=${0.05}
