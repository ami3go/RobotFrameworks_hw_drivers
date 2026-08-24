*** Settings ***
Library    rf_keysight349xx.library.Keysight349xxLibrary
*** Test Cases ***
List Capabilities Offline
    ${caps}=    Get Driver Capabilities
    Log    ${caps}
