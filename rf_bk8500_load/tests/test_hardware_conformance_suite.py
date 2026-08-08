"""Static delivery checks for the physical-device all-keyword Robot suite."""

from __future__ import annotations

from pathlib import Path

from bk8500_load.library import BK8500Library

ROOT = Path(__file__).resolve().parent.parent
SUITE = ROOT / "hardware_tests" / "01_all_library_keywords.robot"


def test_hardware_suite_is_delivered_with_launcher_and_safety_documentation():
    assert SUITE.is_file()
    assert (ROOT / "hardware_tests" / "README.md").is_file()
    for suffix in ("ps1", "bat", "sh"):
        assert (ROOT / "scripts" / f"run_hardware_conformance.{suffix}").is_file()


def test_hardware_suite_references_every_public_keyword():
    text = SUITE.read_text(encoding="utf-8")
    public = {
        getattr(attribute, "robot_name")
        for attribute in vars(BK8500Library).values()
        if getattr(attribute, "robot_name", None)
    }
    missing = sorted(name for name in public if name not in text)
    assert not missing, f"Hardware suite omits public keywords: {missing}"


def test_hazardous_actions_are_explicitly_gated():
    text = SUITE.read_text(encoding="utf-8")
    assert "${ALLOW_INPUT_ON}" in text
    assert "${ALLOW_PERSISTENT_WRITES}" in text
    assert "Skip If    not ${ALLOW_INPUT_ON}" in text
    assert text.count("Skip If    not ${ALLOW_PERSISTENT_WRITES}") >= 5
    assert "Set Load Function Unchecked    FIXED" in text
    assert "Set Load Function Unchecked    SHORT" not in text


def test_clean_release_version_is_used():
    from bk8500_load.version import PACKAGE_RELEASE, VERSION

    assert VERSION == "26.17.0"
    assert PACKAGE_RELEASE == "26.17"



def test_hardware_suite_captures_version_and_instrument_evidence():
    text = SUITE.read_text(encoding="utf-8")
    assert "Installed distribution version" in text
    assert "Driver source version" in text
    assert "Robot Framework version" in text
    assert "Python version" in text
    assert "Instrument serial number" in text
    assert "Should Be Equal    ${distribution_version}    ${source_version}" in text


def test_hardware_suite_separates_recall_keyword_from_save_reconfigure_workflow():
    text = SUITE.read_text(encoding="utf-8")
    assert "WF-001 Save Reconfigure And Recall List" in text
    recall_block = text.split("KW-037 Recall Load List File", 1)[1].split(
        "WF-001 Save Reconfigure And Recall List", 1
    )[0]
    assert recall_block.count("Configure Load List") == 1
    assert "Recall Load List File" in recall_block


def test_persistence_workflow_uses_device_accepted_two_step_replacement():
    text = SUITE.read_text(encoding="utf-8")
    block = text.split("WF-001 Save Reconfigure And Recall List", 1)[1].split(
        "KW-038 Set Battery Cutoff Voltage", 1
    )[0]
    assert "[(0.02, 0.1), (0.03, 0.1)]" in block
    assert "${replacement_count}    2" in block
    assert "[(0.02, 0.1)]" not in block


def test_hardware_suite_supports_optional_baud_autodetection():
    text = SUITE.read_text(encoding="utf-8")
    assert "${AUTO_DETECT_BAUDRATE}" in text
    assert "${BAUDRATE_CANDIDATES}" in text
    assert "${PROBE_TIMEOUT}" in text
    assert "auto_detect_baudrate=${AUTO_DETECT_BAUDRATE}" in text
    assert "baudrate_candidates=${BAUDRATE_CANDIDATES}" in text

