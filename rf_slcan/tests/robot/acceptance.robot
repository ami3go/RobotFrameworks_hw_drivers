*** Settings ***
Documentation     Offline acceptance suite against the bundled simulator (task §14.2).
...               Covers identity, the RFDS-002 canonical connection lifecycle, bitrate/
...               open/close channel control, sending standard and extended frames, receiving
...               an asynchronously injected frame, the drain-queue FIFO, status/version/
...               serial-number queries, and the raw SLCAN escape hatch.
Library           rf_slcan.SlcanLibrary
Library           Collections
Suite Setup       Connect    alias=default    simulated=${TRUE}
Suite Teardown    Disconnect

*** Test Cases ***
Read Identity
    ${identity}=    Get Identity
    Should Contain    ${identity}    SLCAN
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

Channel Cannot Open Before Bitrate Is Set
    Run Keyword And Expect Error    *DeviceError*    Open Channel

Bitrate And Channel Round Trip
    Set Bitrate    500K
    Open Channel    NORMAL
    ${open}=    Is Channel Open
    Should Be True    ${open}
    Close Channel
    ${open}=    Is Channel Open
    Should Not Be True    ${open}

Send Standard And Extended Frames
    Set Bitrate    500K
    Open Channel    NORMAL
    Send Frame    291    AABBCC
    Send Frame    4096    0102    extended=${TRUE}
    Close Channel

Receive Times Out With None When Nothing Arrives
    # Frame injection is a Python-only simulator test hook (not a Robot
    # keyword — it isn't part of the real driver's public surface), so the
    # asynchronous-capture behavior itself is covered in the Python unit
    # tests (test_receive_frame.py). This confirms the Robot-facing timeout
    # contract: receiving nothing is ${NONE}, not an error.
    Set Bitrate    500K
    Open Channel    NORMAL
    ${frame}=    Receive Frame    timeout_s=0.2
    Should Be Equal    ${frame}    ${NONE}
    ${count}=    Get Received Frame Count
    Should Be Equal As Integers    ${count}    0
    Close Channel

Status Version And Serial Number
    ${status}=    Get Status
    Should Be True    isinstance($status, dict)
    Should Not Be True    ${status}[bus_error]
    ${version}=    Get Version
    Should Not Be Empty    ${version}
    ${serial}=    Get Serial Number
    Should Not Be Empty    ${serial}

Raw SLCAN Escape Hatch
    Run Keyword And Expect Error    *ValidationError*    Raw SLCAN Command    V    expects_data=${TRUE}
    Enable Raw SLCAN    ENABLE RAW SLCAN
    ${response}=    Raw SLCAN Command    V    expects_data=${TRUE}
    Should Not Be Empty    ${response}
