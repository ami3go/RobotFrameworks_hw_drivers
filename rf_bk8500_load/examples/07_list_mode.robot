*** Settings ***
Documentation    Program and read back a three-step current list.
Resource         resources/bk8500_example.resource
Suite Setup      Prepare Example Load
Suite Teardown   Safe Example Teardown

*** Test Cases ***
Configure Three Step List
    ${steps}=    Evaluate    [(0.25, 0.1), (0.5, 0.1), (0.75, 0.1)]
    Configure Load List    CC    ${steps}    repeat=ONCE    name=DEMO
    Set Load Function    LIST
    ${count}=    Get Load List Step Count
    Should Be Equal As Integers    ${count}    3
