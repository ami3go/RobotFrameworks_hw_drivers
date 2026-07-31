*** Settings ***
Library         rf_phidget_relay.PhidgetRelayLibrary    active_high=${FALSE}
Suite Setup     Connect Relays       ${DEVICE_A_SERIAL}    ${DEVICE_B_SERIAL}
Suite Teardown  Disconnect Relays
*** Variables ***
${DEVICE_A_SERIAL}    123456
${DEVICE_B_SERIAL}    654321
*** Test Cases ***
Use Inverted External Relay Logic
    Close Relay    6
    Relay Should Be Closed    6

