*** Settings ***
Documentation     Connect to an SLCAN adapter (or the bundled simulator) and read its identity.
...               Run against the simulator:
...                   robot --outputdir results examples/01_identify.robot
...               Run against real hardware, override RESOURCE:
...                   robot --outputdir results --variable RESOURCE:/dev/ttyACM0
...                   --variable SIMULATED:False examples/01_identify.robot
Library           rf_slcan.SlcanLibrary
Suite Teardown    Disconnect

*** Variables ***
${RESOURCE}     ${None}
${SIMULATED}    ${TRUE}

*** Test Cases ***
Identify The Adapter
    ${state}=    Connect    resource=${RESOURCE}    simulated=${SIMULATED}
    Should Be True    ${state}[connected]
    Log    Connected: ${state}

    ${identity}=    Get Identity
    Log    Identity: ${identity}

    ${version}=    Get Version
    ${serial}=    Get Serial Number
    Log    Version: ${version}, serial number: ${serial}
