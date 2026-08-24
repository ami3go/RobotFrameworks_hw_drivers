*** Settings ***
Library    rf_keysight349xx.library.Keysight349xxLibrary
*** Test Cases ***
Offline Driver Information
    ${info}=    Get Driver Information
    Log    ${info}
