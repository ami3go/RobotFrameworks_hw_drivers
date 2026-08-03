*** Settings ***
Documentation    Dry-run smoke suite verifying the public library import surface.
Library          rf_bk8500_load.BK8500Library    auto_connect=${FALSE}

*** Test Cases ***
Required Connection Keywords Are Discoverable
    Keyword Should Exist    Open Load Connection
    Keyword Should Exist    Close All Load Connections
    Keyword Should Exist    Get Load Product Information
