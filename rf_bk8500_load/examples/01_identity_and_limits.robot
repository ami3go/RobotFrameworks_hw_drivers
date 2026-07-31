*** Settings ***
Documentation    Read identity and rated limits without enabling the load input.
Resource         resources/bk8500_example.resource
Suite Setup      Open Example Load
Suite Teardown   Safe Example Teardown

*** Test Cases ***
Read Product Identity And Limits
    ${identity}=    Get Load Product Information
    ${limits}=      Get Load Rated Limits
    Log Dictionary    ${identity}
    Log Dictionary    ${limits}
    Should Not Be Empty    ${identity}[model]
