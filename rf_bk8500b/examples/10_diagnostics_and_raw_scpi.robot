*** Settings ***
Library         BK8500BLibrary
Library         OperatingSystem
Suite Setup     Connect To Electronic Load    %{BK8500B_PORT}
Suite Teardown  Disconnect All Electronic Loads

*** Variables ***
${DIAGNOSTIC_JSON}    ${OUTPUT DIR}${/}bk8500b_diagnostic.json

*** Test Cases ***
Collect Diagnostics
    ${health}=    Run Electronic Load Health Check
    Should Be True    ${health}[healthy]
    ${path}=    Export Diagnostic Snapshot    ${DIAGNOSTIC_JSON}
    File Should Exist    ${path}
    ${version}=    Query Raw SCPI    SYSTem:VERSion?
    Log    SCPI version: ${version}
