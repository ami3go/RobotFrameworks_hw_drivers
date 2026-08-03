*** Settings ***
Documentation    RFDS-019 public keyword callability and SimServ protocol-boundary conformance.
Library          rf_votsch_climate_chamber.VotschClimateChamberLibrary    default_resource=SIM::conformance
Library          ../../tests/support/RFDSConformanceHarness.py    ${CURDIR}${/}..${/}..    ${OUTPUT DIR}
Resource         resources/conformance_variables.resource
Resource         resources/conformance_keywords.resource
Suite Setup      Open Conformance Session
Suite Teardown   Run Keywords    Run Keyword And Ignore Error    Safe Shutdown
...              AND    Run Keyword And Ignore Error    Disconnect All

*** Test Cases ***
RFDS-019 Inventory Callability And Protocol Exercise
    [Tags]    rfds-019    simulator    conformance
    Execute All Public Keywords Through Robot
