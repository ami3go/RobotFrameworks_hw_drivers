*** Settings ***
Library         rf_phidget_relay.PhidgetRelayLibrary
Suite Setup     Connect Relays       ${DEVICE_A_SERIAL}    ${DEVICE_B_SERIAL}
Suite Teardown  Disconnect Relays
*** Variables ***
${DEVICE_A_SERIAL}    123456
${DEVICE_B_SERIAL}    654321
*** Test Cases ***
Pulse A Relay
    Pulse Relay    3    0.5
    Relay Should Be Open    3

