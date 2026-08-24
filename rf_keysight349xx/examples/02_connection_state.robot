*** Settings ***
Library    rf_keysight349xx.library.Keysight349xxLibrary
Suite Teardown    Disconnect All
*** Test Cases ***
Inspect Cached And Live State
    Connect    SIM::34972A    alias=daq
    ${cached}=    Get Connection State    alias=daq
    ${live}=      Get Connection State    alias=daq    refresh=True
    Log    cached=${cached} live=${live}
