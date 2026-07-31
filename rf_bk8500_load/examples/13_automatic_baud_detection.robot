*** Settings ***
Documentation    Probe supported BK8500 baud rates using read-only identity queries.
Resource         resources/bk8500_example.resource
Suite Teardown   Safe Example Teardown

*** Test Cases ***
Detect Baud Rate And Read Identity
    [Documentation]    Hardware-only example. The preferred 9600 rate is tried first.
    Skip If    ${SIMULATED}    Set SIMULATED:false and PORT:<port> to run baud detection.
    Open Load Connection    port=${PORT}    baudrate=${BAUDRATE}    model=${MODEL}
    ...    simulated=${FALSE}    alias=example    auto_detect_baudrate=${TRUE}
    ...    baudrate_candidates=${BAUDRATE_CANDIDATES}    probe_timeout=${PROBE_TIMEOUT}
    ${connection}=    Get Load Connection Info
    ${identity}=      Get Load Product Information
    Log Dictionary    ${connection}
    Log Dictionary    ${identity}
    Should Be True    ${connection}[baudrate] in [4800, 9600, 19200, 38400]
    Should Be Equal    ${connection}[baudrate_auto_detected]    ${TRUE}
    Should Not Be Empty    ${identity}[model]
    Should Not Be Empty    ${identity}[serial_number]
