*** Settings ***
Library         rf_phidget_relay.PhidgetRelayLibrary
Suite Setup     Connect Relays       ${DEVICE_A_SERIAL}    ${DEVICE_B_SERIAL}
Suite Teardown  Disconnect Relays

*** Variables ***
${DEVICE_A_SERIAL}    123456
${DEVICE_B_SERIAL}    654321

*** Test Cases ***
Connect With Safe Defaults
    Open All Relays

