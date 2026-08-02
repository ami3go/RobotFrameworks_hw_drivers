*** Settings ***
Documentation     Set the CAN bitrate, open the channel, and transmit standard/extended/
...               remote frames. The channel cannot be opened before a bitrate is set —
...               that's a fail-closed judgment call documented in the task doc, not an
...               oversight.
Library           rf_slcan.SlcanLibrary
Suite Setup       Connect    simulated=${TRUE}
Suite Teardown    Disconnect

*** Test Cases ***
Open Fails Without A Bitrate First
    Run Keyword And Expect Error    *DeviceError*    Open Channel

Configure The Bus And Transmit
    Set Bitrate    500K
    Open Channel    NORMAL

    # Standard (11-bit) data frame.
    Send Frame    291    AABBCCDD

    # Extended (29-bit) data frame.
    Send Frame    4096    0102    extended=${TRUE}

    # Remote (RTR) frame requesting 4 bytes from arbitration ID 0x321 — no data payload.
    Send Frame    801    remote=${TRUE}

    Close Channel

Listen-Only Mode Rejects Transmission
    Set Bitrate    250K
    Open Channel    LISTEN_ONLY
    Run Keyword And Expect Error    *DeviceError*    Send Frame    291    AA
    Close Channel
