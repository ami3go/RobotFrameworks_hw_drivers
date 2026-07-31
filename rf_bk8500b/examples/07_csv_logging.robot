*** Settings ***
Library         BK8500BLibrary
Library         OperatingSystem
Suite Setup     Connect To Electronic Load    %{BK8500B_PORT}
Suite Teardown  Disconnect All Electronic Loads
Test Teardown   Disable Electronic Load Input

*** Variables ***
${OUTPUT_CSV}    ${OUTPUT DIR}${/}bk8500b_measurements.csv

*** Test Cases ***
Log Ten Samples
    Configure And Enable Load    CC    0.5    current_limit=0.7
    ${path}=    Log Measurements To CSV    ${OUTPUT_CSV}    samples=10    interval=1.0
    File Should Exist    ${path}
