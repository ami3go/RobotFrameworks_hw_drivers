*** Settings ***
Documentation     Acceptance code/mask filter configuration and timestamp mode (Gate 3).
...               Neither is confirmed as universally supported/identical across SLCAN
...               adapters (task doc §2/§16) — grounded in the widely-mirrored Lawicel
...               description. Both are host-tracked, read-only round trips: the adapter has
...               no query form for either, so Get Acceptance Code/Mask/Timestamps Enabled
...               simply report what this driver last successfully set.
Library           rf_slcan.SlcanLibrary
Suite Setup       Connect    simulated=${TRUE}
Suite Teardown    Disconnect

*** Test Cases ***
Configure An Acceptance Filter Before Opening
    # M/m are only accepted while the channel is closed, mirroring the
    # confirmed S<n> bitrate constraint.
    Set Acceptance Code    0x100
    Set Acceptance Mask    0x7FF
    ${code}=    Get Acceptance Code
    ${mask}=    Get Acceptance Mask
    Log    Acceptance code=${code} mask=${mask}

    Set Bitrate    500K
    Open Channel    NORMAL
    Run Keyword And Expect Error    *DeviceError*    Set Acceptance Code    0x200
    Close Channel

Enable Timestamps On Received Frames
    Set Timestamps Enabled    ${TRUE}
    ${enabled}=    Get Timestamps Enabled
    Should Be True    ${enabled}

    Set Bitrate    500K
    Open Channel    NORMAL
    ${frame}=    Receive Frame    timeout_s=0.5
    IF    $frame is not None
        Log    Received at timestamp ${frame}[timestamp_ms] ms
    ELSE
        Log    No frame arrived within the timeout — a normal outcome on a quiet bus.
    END
    Close Channel

    Set Timestamps Enabled    ${FALSE}
