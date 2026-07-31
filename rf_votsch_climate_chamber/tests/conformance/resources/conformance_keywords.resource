*** Keywords ***
Open Conformance Session
    ${state}=    Connect    resource=${CONFORMANCE_RESOURCE}    alias=${CONFORMANCE_ALIAS}    timeout_s=${CONFORMANCE_TIMEOUT}
    RETURN    ${state}

Close Conformance Session
    Run Keyword And Ignore Error    Safe Shutdown    alias=${CONFORMANCE_ALIAS}
    Run Keyword And Ignore Error    Disconnect    alias=${CONFORMANCE_ALIAS}
