"""Project delivery structure checks for the outer RFDS source package."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_mandatory_project_directories_exist():
    for name in ("bk8500_load", "ai", "history", "review", "examples", "hardware_tests", "evidence", "scripts", "guide", "docs"):
        assert (ROOT / name).is_dir(), f"Missing mandatory project directory: {name}/"


def test_at_least_ten_robot_examples_are_delivered():
    examples = sorted((ROOT / "examples").glob("[0-9][0-9]_*.robot"))
    assert len(examples) >= 10


def test_cross_platform_example_runners_exist():
    expected = {
        "run_all_examples.bat",
        "run_all_examples.ps1",
        "run_all_examples.sh",
        "run_example.bat",
        "run_example.ps1",
        "run_example.sh",
    }
    present = {path.name for path in (ROOT / "scripts").iterdir() if path.is_file()}
    assert expected <= present


def test_github_pages_entry_point_exists():
    assert (ROOT / "docs" / "index.md").is_file()
    assert (ROOT / "docs" / "_config.yml").is_file()


def test_pycharm_robot_guide_exists():
    assert (ROOT / "guide" / "pycharm_robot_framework_setup.md").is_file()


def test_flat_source_layout_has_no_src_directory():
    assert not (ROOT / "src").exists(), "src/ level must not be present"
    assert (ROOT / "bk8500_load" / "library.py").is_file()
    assert (ROOT / "BK8500Library.py").is_file()


def test_root_ai_delivery_is_complete():
    required = {
        "README.md",
        "bk8500_load_ai_contract.yaml",
        "bk8500_load_ai_contract.lock",
        "system_ai_contract.example.yaml",
        "RFDS-017_AI_Driver_Contract_v3.0.md",
        "RFDS-018_AI_Test_Bench_Contract_v1.0.md",
        "RFDS-019_Robot_Framework_Driver_Call_and_Protocol_Conformance_Test_Specification_v1.1.md",
        "RFDS_Driver_Implementation_Lifecycle_v1.1.md",
    }
    present = {path.name for path in (ROOT / "ai").iterdir() if path.is_file()}
    assert required <= present


def test_examples_directory_has_direct_cross_platform_wrappers():
    expected = {
        "run_all_examples.bat",
        "run_all_examples.ps1",
        "run_all_examples.sh",
        "run_example.bat",
        "run_example.ps1",
        "run_example.sh",
    }
    present = {path.name for path in (ROOT / "examples").iterdir() if path.is_file()}
    assert expected <= present


def test_powershell_runners_verify_private_environment():
    ensure = (ROOT / "scripts" / "ensure_environment.ps1").read_text(encoding="utf-8")
    single = (ROOT / "scripts" / "run_example.ps1").read_text(encoding="utf-8")
    all_examples = (ROOT / "scripts" / "run_all_examples.ps1").read_text(encoding="utf-8")
    assert "import robot, serial, bk8500_load" in ensure
    assert "m.version('bk8500-load') == bk8500_load.__version__" in ensure
    assert "setup_venv.ps1" in ensure
    assert "ensure_environment.ps1" in single
    assert "ensure_environment.ps1" in all_examples


def test_setup_installs_runtime_dependencies_from_project_metadata():
    setup = (ROOT / "scripts" / "setup_venv.ps1").read_text(encoding="utf-8")
    metadata = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'pip install -e ".[dev]"' in setup
    assert '"robotframework>=6.0"' in metadata
    assert '"pyserial>=3.4"' in metadata


def test_short_name_shim_defines_the_library_class_locally():
    import importlib
    from bk8500_load.library import BK8500Library as Implementation

    module = importlib.import_module("BK8500Library")
    public = module.BK8500Library
    assert public.__module__ == "BK8500Library"
    assert issubclass(public, Implementation)
    assert getattr(public.open_load_connection, "robot_name", None) == "Open Load Connection"
    assert getattr(public.close_all_load_connections, "robot_name", None) == "Close All Load Connections"


def test_environment_validation_dry_runs_public_library_import():
    smoke = ROOT / "scripts" / "verify_library_import.robot"
    assert smoke.is_file()
    text = smoke.read_text(encoding="utf-8")
    assert "Library          BK8500Library" in text
    assert "Open Load Connection" in text
    assert "Close All Load Connections" in text
    assert "verify_library_import.robot" in (ROOT / "scripts" / "ensure_environment.ps1").read_text(encoding="utf-8")
    assert "verify_library_import.robot" in (ROOT / "scripts" / "ensure_environment.sh").read_text(encoding="utf-8")


def test_examples_import_collections_for_dictionary_logging():
    resource = (ROOT / "examples" / "resources" / "bk8500_example.resource").read_text(encoding="utf-8")
    assert "Library    Collections" in resource
    for example in (ROOT / "examples").glob("[0-9][0-9]_*.robot"):
        text = example.read_text(encoding="utf-8")
        if "Log Dictionary" in text:
            assert "Resource         resources/bk8500_example.resource" in text, (
                f"{example.name} uses Log Dictionary without the shared Collections import"
            )


def test_environment_validation_dry_runs_all_examples():
    powershell = (ROOT / "scripts" / "ensure_environment.ps1").read_text(encoding="utf-8")
    shell = (ROOT / "scripts" / "ensure_environment.sh").read_text(encoding="utf-8")
    batch = (ROOT / "scripts" / "run_example.bat").read_text(encoding="utf-8")
    assert 'Join-Path $Root "examples"' in powershell
    assert '"$ROOT/examples"' in shell
    assert '"%ROOT%\\examples"' in batch



def test_environment_validation_dry_runs_hardware_suite_and_checks_version_match():
    powershell = (ROOT / "scripts" / "ensure_environment.ps1").read_text(encoding="utf-8")
    shell = (ROOT / "scripts" / "ensure_environment.sh").read_text(encoding="utf-8")
    assert "hardware_tests\\01_all_library_keywords.robot" in powershell
    assert "hardware_tests/01_all_library_keywords.robot" in shell
    assert "bk8500-load" in powershell and "bk8500_load.__version__" in powershell
    assert "bk8500-load" in shell and "bk8500_load.__version__" in shell


def test_hardware_runner_writes_software_version_evidence():
    powershell = (ROOT / "scripts" / "run_hardware_conformance.ps1").read_text(encoding="utf-8")
    assert "software_versions.json" in powershell
    assert "importlib.metadata.version('bk8500-load')" in powershell


def test_serial_echo_diagnostic_and_runners_are_delivered():
    assert (ROOT / "hardware_tests" / "02_serial_echo_diagnostic.py").is_file()
    for name in (
        "run_serial_diagnostic.ps1",
        "run_serial_diagnostic.bat",
        "run_serial_diagnostic.sh",
    ):
        assert (ROOT / "scripts" / name).is_file()


def test_preserved_hardware_evidence_is_complete():
    import csv
    import json
    import xml.etree.ElementTree as ET

    evidence = (
        ROOT
        / "evidence"
        / "hardware_conformance"
        / "v26.14_com12_2026-07-28"
    )
    required = {
        "README.md",
        "conformance_summary.md",
        "device_identity.json",
        "environment.json",
        "evidence_manifest.sha256",
        "expected_negative_messages.json",
        "keyword_coverage.csv",
        "log.html",
        "output.xml",
        "report.html",
    }
    assert required <= {item.name for item in evidence.iterdir() if item.is_file()}

    environment = json.loads((evidence / "environment.json").read_text(encoding="utf-8"))
    identity = json.loads((evidence / "device_identity.json").read_text(encoding="utf-8"))
    assert environment["driver_source_version"] == "26.14.0"
    assert environment["installed_distribution_version"] == "26.14.0"
    assert environment["test_count"] == 56
    assert environment["passed"] == 56
    assert environment["failed"] == 0
    assert identity["model"] == "8500"
    assert identity["serial_number"] == "1687710135"
    assert identity["firmware_version"] == "1.84"

    with (evidence / "keyword_coverage.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 56
    assert all(row["status"] == "PASS" for row in rows)
    assert sum(row["category"] == "keyword" for row in rows) == 55
    assert sum(row["category"] == "workflow" for row in rows) == 1

    root = ET.parse(evidence / "output.xml").getroot()
    test_statuses = []
    for test in root.iter("test"):
        status = next(child for child in test if child.tag == "status")
        test_statuses.append(status.attrib["status"])
    assert len(test_statuses) == 56
    assert set(test_statuses) == {"PASS"}


def test_automatic_baud_detection_delivery_is_documented_and_runnable():
    assert (ROOT / "examples" / "13_automatic_baud_detection.robot").is_file()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    release = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    contract = (ROOT / "ai" / "bk8500_load_ai_contract.yaml").read_text(encoding="utf-8")
    assert "baudrate=AUTO" in readme
    assert "auto_detect_baudrate" in release
    assert "confirm_baudrate_identity" in contract
    for name in ("ps1", "bat", "sh"):
        runner = (ROOT / "scripts" / f"run_hardware_conformance.{name}").read_text(encoding="utf-8")
        assert "AUTO_DETECT" in runner.upper()

