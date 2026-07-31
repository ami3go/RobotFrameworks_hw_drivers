*** Settings ***
Library         rf_phidget_relay.PhidgetRelayLibrary
Suite Setup     Connect Relays       ${DEVICE_A_SERIAL}    ${DEVICE_B_SERIAL}
Suite Teardown  Disconnect Relays
*** Variables ***
${DEVICE_A_SERIAL}    123456
${DEVICE_B_SERIAL}    654321
&{STATES}    1=ON    2=OFF    5=CLOSED    8=OPEN
*** Test Cases ***
Apply Selected States
    Set Multiple Relays    ${STATES}

