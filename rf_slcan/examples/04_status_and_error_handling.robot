*** Settings ***
Documentation     Status flags, the raw SLCAN escape hatch, and the typed errors this driver
...               raises for the mistakes a script can actually make (opening before a bitrate
...               is set, transmitting while not open, transmitting in listen-only mode).
Library           rf_slcan.SlcanLibrary
Suite Setup       Connect    simulated=${TRUE}
Suite Teardown    Disconnect

*** Test Cases ***
Read Adapter Status
    ${status}=    Get Status
    Log    Status: ${status}
    IF    ${status}[bus_error] or ${status}[error_passive] or ${status}[arbitration_lost]
        Log    Bus fault reported by the adapter    level=WARN
    END

Typed Errors For Common Mistakes
    Run Keyword And Expect Error    *DeviceError*    Open Channel
    Set Bitrate    500K
    Run Keyword And Expect Error    *DeviceError*    Send Frame    291    AA
    Open Channel    NORMAL
    Run Keyword And Expect Error    *ValidationError*    Send Frame    291    ${{[0] * 9}}
    Close Channel

Closing Is Always Safe Even If Not Open
    # task §6: the channel must always be closeable, even mid-fault or when
    # the driver's own state already believes it's closed.
    Close Channel
    Close Channel

Raw SLCAN Escape Hatch For Anything Not Yet Typed
    Run Keyword And Expect Error    *ValidationError*    Raw SLCAN Command    F    expects_data=${TRUE}
    Enable Raw SLCAN    ENABLE RAW SLCAN
    ${status_line}=    Raw SLCAN Command    F    expects_data=${TRUE}
    Log    Raw status response: ${status_line}
