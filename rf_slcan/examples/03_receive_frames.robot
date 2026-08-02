*** Settings ***
Documentation     Receive CAN frames from the bus. ``Receive Frame`` blocks up to a timeout
...               and returns ${NONE} on timeout rather than raising — receiving nothing is a
...               normal outcome, not an error. Frames arrive via a background reader thread,
...               so they're captured even between keyword calls, not just while a keyword is
...               actively running.
...               Run against the simulator:
...                   robot --outputdir results examples/03_receive_frames.robot
...               Run against real hardware, override RESOURCE (and connect a bus with some
...               other node transmitting, or this will simply time out — which is itself a
...               valid, demonstrated outcome):
...                   robot --outputdir results --variable RESOURCE:/dev/ttyACM0
...                   --variable SIMULATED:False examples/03_receive_frames.robot
Library           rf_slcan.SlcanLibrary
Suite Setup       Connect    resource=${RESOURCE}    simulated=${SIMULATED}
Suite Teardown    Disconnect

*** Variables ***
${RESOURCE}     ${None}
${SIMULATED}    ${TRUE}

*** Test Cases ***
Wait For A Single Frame
    Set Bitrate    500K
    Open Channel    NORMAL
    ${frame}=    Receive Frame    timeout_s=1
    IF    $frame is None
        Log    No frame arrived within the timeout — a normal outcome on a quiet bus.
    ELSE
        Log    Received: ID=${frame}[arbitration_id] data=${frame}[data]
    END
    Close Channel

Drain Whatever Has Queued Up
    Set Bitrate    500K
    Open Channel    NORMAL
    Sleep    0.5s    # give the background reader a moment to capture any bus traffic
    ${frames}=    Drain Received Frames
    ${count}=    Get Length    ${frames}
    Log    Drained ${count} frame(s)
    ${overflow}=    Get Receive Overflow Count
    Should Be Equal As Integers    ${overflow}    0    msg=Receive queue overflowed — frames were dropped
    Close Channel
