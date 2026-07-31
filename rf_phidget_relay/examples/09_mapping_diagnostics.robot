*** Settings ***
Library         rf_phidget_relay.PhidgetRelayLibrary
Library         Collections
Suite Setup     Connect Relays       ${DEVICE_A_SERIAL}    ${DEVICE_B_SERIAL}
Suite Teardown  Disconnect Relays
*** Variables ***
${DEVICE_A_SERIAL}    123456
${DEVICE_B_SERIAL}    654321
*** Test Cases ***
Show Physical Mapping
    ${mapping}=    Get Relay Mapping
    Log Dictionary    ${mapping}

