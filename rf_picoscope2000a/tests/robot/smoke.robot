*** Settings ***
Documentation     Offline smoke suite against the bundled simulator. Covers identity, the
...               RFDS-002 canonical connection lifecycle, autodetect, channel
...               configuration including the current-probe abstraction, trigger and
...               timebase setup, a block capture with waveform/CSV/image export (single
...               channel and all channels), AWG control, and a preset save/load round trip.
Library           rf_picoscope2000a.PicoScope2000ALibrary
Library           OperatingSystem
Library           Collections
Suite Setup       Connect    alias=default    simulated=${TRUE}
Suite Teardown    Disconnect

*** Variables ***
${WAVEFORM_CSV}       ${OUTPUT DIR}/waveform_a.csv
${ALL_WAVEFORMS_CSV}    ${OUTPUT DIR}/waveform_all.csv
${CHANNEL_IMAGE}      ${OUTPUT DIR}/channel_a.png
${ALL_CHANNELS_IMAGE}    ${OUTPUT DIR}/channels_all.png
${PRESET_FILE}        ${OUTPUT DIR}/preset.json

*** Test Cases ***
Read Identity
    ${identity}=    Get Identity
    Should Contain    ${identity}    Pico Technology
    Should Not Be Empty    ${identity}

Connect Is Idempotent For The Same Resource
    ${first}=    Connect    alias=default    simulated=${TRUE}
    ${second}=    Connect    alias=default    simulated=${TRUE}
    Should Be Equal    ${first}[identity]    ${second}[identity]

Is Connected And Get Connection State
    ${connected}=    Is Connected
    Should Be True    ${connected}
    ${state}=    Get Connection State
    Should Be Equal    ${state}[state]    connected

Check Communication
    ${ok}=    Check Communication
    Should Be True    ${ok}

Find Devices Lists The Simulated Serial
    ${devices}=    Find Devices
    List Should Contain Value    ${devices}    SIM/00001

Configure Channel A As A Voltage Channel
    Set Channel Enabled    A    ${TRUE}
    Set Channel Range    A    5.0
    Set Channel Coupling    A    DC
    Set Channel Offset    A    0.0
    ${settings}=    Get Channel Settings    A
    Should Be True    ${settings}[enabled]
    Should Be Equal As Numbers    ${settings}[range_v]    5.0

Configure Channel B With A Current Probe
    Set Channel Enabled    B    ${TRUE}
    Set Channel Probe    B    current    scale=10.0
    ${probe}=    Get Channel Probe    B
    Should Be Equal    ${probe}[probe_type]    CURRENT
    Should Be Equal As Numbers    ${probe}[probe_scale]    10.0

Configure Trigger
    Set Trigger    A    threshold_v=0.5    direction=RISING
    ${settings}=    Get Trigger Settings
    Should Be True    ${settings}[enabled]
    Should Be Equal    ${settings}[channel]    A
    [Teardown]    Disable Trigger

Configure Timebase
    ${settings}=    Set Timebase    sample_interval_s=${0.00002}    num_samples=${200}
    Should Be Equal As Integers    ${settings}[num_samples]    200

Capture And Fetch Waveforms
    ${summary}=    Capture Block
    List Should Contain Value    ${summary}[channels]    A
    List Should Contain Value    ${summary}[channels]    B
    ${waveform_a}=    Get Waveform    A
    Should Be Equal    ${waveform_a}[unit]    V
    ${waveform_b}=    Get Waveform    B
    Should Be Equal    ${waveform_b}[unit]    A
    ${all_waveforms}=    Get All Waveforms
    Dictionary Should Contain Key    ${all_waveforms}    A
    Dictionary Should Contain Key    ${all_waveforms}    B

Get Standard Measurements
    ${measurements}=    Get Measurements    A
    Dictionary Should Contain Key    ${measurements}    amplitude
    Dictionary Should Contain Key    ${measurements}    frequency_hz
    ${frequency}=    Get Measurement    A    FREQUENCY
    Should Be True    ${frequency} > 0
    Measurement Should Be Within    A    PK2Pk    ${0}    ${10}

Get Cross-Channel Timing
    ${delay}=    Get Channel Delay    A    B
    ${phase}=    Get Channel Phase    A    B
    Channel Delay Should Be Within    A    B    ${{$delay - 0.000001}}    ${{$delay + 0.000001}}
    Channel Phase Should Be Within    A    B    ${{$phase - 1}}    ${{$phase + 1}}

Save Waveform CSVs
    Save Waveform To CSV    ${WAVEFORM_CSV}    A
    File Should Exist    ${WAVEFORM_CSV}
    Save All Waveforms To CSV    ${ALL_WAVEFORMS_CSV}
    File Should Exist    ${ALL_WAVEFORMS_CSV}

Save Waveform Images If Matplotlib Is Installed
    [Documentation]    The ``plot`` extra is optional; skip cleanly if it isn't installed.
    ${status}=    Run Keyword And Return Status
    ...    Save Channel Image    ${CHANNEL_IMAGE}    A
    IF    ${status}
        File Should Exist    ${CHANNEL_IMAGE}
        Save All Channels Image    ${ALL_CHANNELS_IMAGE}
        File Should Exist    ${ALL_CHANNELS_IMAGE}
    ELSE
        Log    matplotlib not installed; skipping image export checks    level=WARN
    END

Control The AWG
    Set AWG Waveform    sine    frequency_hz=1000    peak_to_peak_v=1.0
    ${settings}=    Get AWG Settings
    Should Be True    ${settings}[enabled]
    Should Be Equal    ${settings}[wave_type]    SINE
    Stop AWG
    ${stopped}=    Get AWG Settings
    Should Not Be True    ${stopped}[enabled]

Save And Load A Preset
    Set Channel Enabled    A    ${TRUE}
    Set Channel Range    A    2.0
    Save Preset    ${PRESET_FILE}
    File Should Exist    ${PRESET_FILE}
    Connect    alias=fresh    simulated=${TRUE}
    Load Preset    ${PRESET_FILE}    alias=fresh
    ${settings}=    Get Channel Settings    A    alias=fresh
    Should Be Equal As Numbers    ${settings}[range_v]    2.0
    [Teardown]    Disconnect    alias=fresh

Export Diagnostic Bundle
    ${bundle}=    Export Diagnostic Bundle
    Should Not Be Empty    ${bundle}
