*** Settings ***
Documentation     Fetch a waveform, save a screen image, export a CSV, and save/restore
...               the instrument setup — the four evidence-capture keywords from task §10.
Library           rf_tbs1000c.Tbs1000cLibrary
Library           OperatingSystem
Suite Setup       Connect    simulated=${TRUE}
Suite Teardown    Disconnect

*** Variables ***
${SCREEN_IMAGE}    ${OUTPUT DIR}/example_screen.png
${WAVEFORM_CSV}     ${OUTPUT DIR}/example_waveform.csv
${SETUP_FILE}       ${OUTPUT DIR}/example_setup.txt

*** Test Cases ***
Capture A Waveform And Save Evidence
    ${waveform}=    Get Waveform    1
    Log    Captured ${{len($waveform["time_s"])}} points

    Save Screen Image    ${SCREEN_IMAGE}
    File Should Exist    ${SCREEN_IMAGE}

    Save Waveform To CSV    ${WAVEFORM_CSV}    1
    File Should Exist    ${WAVEFORM_CSV}

Save And Restore A Known Configuration
    Set Channel Scale    1    0.2
    Save Setup    ${SETUP_FILE}

    Set Channel Scale    1    5.0
    Restore Setup    ${SETUP_FILE}

    ${scale}=    Get Channel Scale    1
    Should Be Equal As Numbers    ${scale}    0.2
