*** Settings ***
Documentation    RFDS-014 configuration validation and profile example.
Library    rf_votsch_climate_chamber.VotschClimateChamberLibrary    managed_configuration_root=${OUTPUT DIR}${/}profiles

*** Test Cases ***
Validate Save And Load Configuration
    ${default}=    Get Driver Default Configuration
    ${validation}=    Validate Driver Configuration    ${default}
    Should Be True    ${validation}[valid]
    Save Driver Configuration    example    overwrite=${TRUE}
    ${profiles}=    List Driver Configuration Profiles
    Should Not Be Empty    ${profiles}
    Load Driver Configuration    example
    Delete Driver Configuration Profile    example    confirm=${TRUE}
