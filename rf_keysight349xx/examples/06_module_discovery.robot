*** Settings ***
Library    rf_keysight349xx.library.Keysight349xxLibrary
Suite Teardown    Disconnect All
*** Test Cases ***
Discover Modules
    Connect    SIM::34972A    alias=daq
    ${modules}=    Get Installed Modules    alias=daq
    Log Many    @{modules}
