*** Settings ***
Library         rf_phidget_relay.PhidgetRelayLibrary
Suite Setup     Connect Relays       ${DEVICE_A_SERIAL}    ${DEVICE_B_SERIAL}
Suite Teardown  Disconnect Relays
*** Variables ***
${DEVICE_A_SERIAL}    123456
${DEVICE_B_SERIAL}    654321
*** Test Cases ***
Operate Channel Eight On Device B
    Close Relay    8
    ${state}=    Get Relay State    8
    Should Be Equal    ${state}    CLOSED

