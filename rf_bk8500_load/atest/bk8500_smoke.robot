*** Settings ***
Documentation     Driver conformance suite for the B&K 8500 series DC load.
...               Each test maps to a verification objective in ai/ai_contract.yaml.
Resource          resources/bk8500_common.resource
Suite Setup       Connect To DC Load
Suite Teardown    Disconnect From DC Load
Test Teardown     Return Load To Idle
Force Tags        bk8500    driver


*** Test Cases ***
Instrument Identity Is Readable
    [Documentation]    VO-IDENT: the load answers 0x6A with a plausible identity.
    [Tags]    identity    no_current
    ${info}=    Get Load Product Information
    Should Not Be Empty    ${info}[model]
    Should Not Be Empty    ${info}[serial_number]
    Should Match Regexp    ${info}[firmware_version]    ^[0-9A-F]+\\.[0-9A-F]+$

Protection Limits Round Trip
    [Documentation]    VO-PROT-RT: written limits read back within one LSB.
    [Tags]    protection    no_current
    Configure Load Protection    max_voltage=${18}    max_current=${4}    max_power=${80}
    ${limits}=    Get Load Protection Limits
    Should Be Equal As Numbers    ${limits}[max_voltage_v]    ${18}
    Should Be Equal As Numbers    ${limits}[max_current_a]    ${4}
    Should Be Equal As Numbers    ${limits}[max_power_w]      ${80}
    [Teardown]    Configure Load Protection    max_voltage=${MAX_VOLTAGE}
    ...    max_current=${MAX_CURRENT}    max_power=${MAX_POWER}

Mode Selection Round Trips For Every Mode
    [Documentation]    VO-MODE-RT: 0x28 and 0x29 agree for CC, CV, CW and CR.
    [Tags]    mode    no_current
    FOR    ${mode}    IN    CC    CV    CW    CR
        Set Load Mode    ${mode}
        Load Mode Should Be    ${mode}
    END

Setpoints Round Trip Within Resolution
    [Documentation]    VO-SETPOINT-RT: setpoint readback matches within one count.
    [Tags]    setpoint    no_current
    Set Load Setpoint    CC    ${2.5}
    ${cc}=    Get Load Setpoint    CC
    Should Be Equal As Numbers    ${cc}    ${2.5}    precision=4
    Set Load Setpoint    CV    ${5.0}
    ${cv}=    Get Load Setpoint    CV
    Should Be Equal As Numbers    ${cv}    ${5.0}    precision=3

Input Off Sinks No Current
    [Documentation]    VO-INPUT-OFF: with the input open the load draws ~0 A.
    [Tags]    input    safety
    Load Input Off
    Load Input State Should Be    OFF
    Load Current Should Be Within    ${0}    ${0.005}

Constant Current Regulation Is Within Tolerance
    [Documentation]    VO-CC-REG: measured sink current tracks the CC setpoint.
    [Tags]    cc    regulation
    Sink And Settle    ${2.0}
    Load Input State Should Be    ON
    Load Current Should Be Within    ${2.0}    ${0.05}
    Load Should Report No Protection Faults

Constant Resistance Regulation Follows Ohms Law
    [Documentation]    VO-CR-REG: I = V / R at the terminals within tolerance.
    [Tags]    cr    regulation
    Apply Constant Resistance    ${6.0}    enable_input=${TRUE}
    Wait Until Load Reading Is Stable    quantity=current    tolerance=${0.02}
    ...    window=${0.2}    timeout=${5}    interval=${0.05}
    ${reading}=    Measure Load Input
    ${expected}=    Evaluate    ${reading}[voltage_v] / 6.0
    Load Current Should Be Within    ${expected}    ${0.05}

Measured Power Agrees With Voltage Times Current
    [Documentation]    VO-POWER-CONSISTENCY: P equals V*I within 2 %.
    [Tags]    measurement
    Sink And Settle    ${1.5}
    ${reading}=    Measure Load Input
    ${product}=    Evaluate    ${reading}[voltage_v] * ${reading}[current_a]
    ${tolerance}=    Evaluate    max(0.02 * ${product}, 0.05)
    Load Power Should Be Within    ${product}    ${tolerance}

Transient Parameters Round Trip
    [Documentation]    VO-TRAN-RT: A/B levels and dwell times survive readback.
    [Tags]    transient    no_current
    Configure Load Transient    CC    ${1.0}    ${0.01}    ${2.0}    ${0.02}    operation=PULSE
    ${transient}=    Get Load Transient    CC
    Should Be Equal As Numbers    ${transient}[level_a]    ${1.0}    precision=4
    Should Be Equal As Numbers    ${transient}[dwell_a_s]    ${0.01}    precision=5
    Should Be Equal As Numbers    ${transient}[level_b]    ${2.0}    precision=4
    Should Be Equal As Numbers    ${transient}[dwell_b_s]    ${0.02}    precision=5
    Should Be Equal    ${transient}[operation]    PULSE

List Sequence Round Trips
    [Documentation]    VO-LIST-RT: a programmed list reads back step by step.
    [Tags]    list    no_current
    ${steps}=    Evaluate    [(0.5, 0.05), (1.5, 0.10), (2.5, 0.15)]
    Configure Load List    CC    ${steps}    repeat=ONCE    name=SMOKE
    ${count}=    Get Load List Step Count
    Should Be Equal As Integers    ${count}    3
    ${step}=    Get Load List Step    CC    ${2}
    Should Be Equal As Numbers    ${step}[level]    ${1.5}    precision=4
    Should Be Equal As Numbers    ${step}[dwell_s]    ${0.10}    precision=5

Bus Trigger Is Accepted Only When Selected
    [Documentation]    VO-TRIG: 0x5A is rejected unless the source is BUS.
    [Tags]    trigger    no_current
    Set Load Trigger Source    IMMEDIATE
    Run Keyword And Expect Error    *rejected by the instrument*    Trigger Load
    Set Load Trigger Source    BUS
    Get Load Trigger Source
    Trigger Load

Over Range Setpoint Is Rejected Before Transmission
    [Documentation]    VO-GUARD: driver-side validation protects the DUT.
    [Tags]    safety    no_current
    ${limits}=    Get Load Rated Limits
    ${too_much}=    Evaluate    ${limits}[max_current_a] + 1
    Run Keyword And Expect Error    *outside the permitted range*
    ...    Set Load Setpoint    CC    ${too_much}

Short Function Requires An Explicit Override
    [Documentation]    VO-SHORT-GUARD: SHORT is not reachable by accident.
    [Tags]    safety    no_current
    Run Keyword And Expect Error    *SHORT function is not available*
    ...    Set Load Function    SHORT

Safe State Teardown Opens The Input
    [Documentation]    VO-TEARDOWN: the teardown contract always de-energises.
    [Tags]    safety
    Sink And Settle    ${1.0}
    Reset Load To Safe State
    Claim Remote Control
    Load Input State Should Be    OFF
    ${function}=    Get Load Function
    Should Be Equal    ${function}    FIXED

Deliberate Over Current Trip Is Reported
    [Documentation]    VO-PROTECTION-TRIP: the demand-state register surfaces an
    ...                over-current condition. Excluded by default on hardware:
    ...                run with --exclude deliberate_fault unless the bench and
    ...                DUT are authorised for a deliberate protection trip.
    [Tags]    protection    deliberate_fault
    Configure Load Protection    max_current=${1.0}
    Apply Constant Current    ${3.0}    enable_input=${TRUE}
    Run Keyword And Expect Error    *over_current*    Load Should Report No Protection Faults
    [Teardown]    Run Keywords    Return Load To Idle
    ...    AND    Configure Load Protection    max_current=${MAX_CURRENT}
