#!/usr/bin/env python3
"""Validate, build, inventory, and package the fixed-root release."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rf_votsch_climate_chamber.version import (
    API_VERSION,
    PEP440_VERSION,
    RELEASE_CLASS,
    RELEASE_LABEL,
    RELEASE_VERSION,
)

NAME = "rf_votsch_climate_chamber"
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "__pycache__",
    "site",
    "build",
    "results",
    ".idea",
}
EXCLUDED_FILES = {".coverage", ".DS_Store"}


def run(*args: object, capture: bool = False) -> subprocess.CompletedProcess[str]:
    command = [str(arg) for arg in args]
    print("+", " ".join(command))
    return subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=capture,
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def included(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return (
        path.is_file()
        and not any(part in EXCLUDED_PARTS or part.endswith(".egg-info") for part in relative.parts)
        and path.suffix not in {".pyc", ".pyo"}
        and path.name not in EXCLUDED_FILES
    )


def clean_generated_outputs() -> None:
    for name in ("dist", "build", "release"):
        shutil.rmtree(ROOT / name, ignore_errors=True)
    for path in ROOT.glob("*.egg-info"):
        shutil.rmtree(path, ignore_errors=True)
    (ROOT / "release").mkdir()


def build_distributions() -> tuple[Path, Path]:
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    from setuptools import build_meta

    sdist_name = build_meta.build_sdist(str(dist))
    wheel_name = build_meta.build_wheel(str(dist))
    return dist / wheel_name, dist / sdist_name


def clean_install_smoke(wheel: Path) -> None:
    environment = Path(tempfile.mkdtemp(prefix="rf_vcc_release_venv_"))
    try:
        run(sys.executable, "-m", "venv", "--system-site-packages", environment)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run(
            [str(python), "-m", "pip", "install", "--no-deps", "--force-reinstall", str(wheel)],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        code = (
            "from importlib.metadata import entry_points,version; "
            "assert version('rf-votsch-climate-chamber')=='" + PEP440_VERSION + "'; "
            "eps=[e for e in entry_points(group='rfds.drivers') if e.name=='votsch.climate_chamber']; "
            "assert len(eps)==1; "
            "lib=eps[0].load().create_library(config={'default_resource':'SIM::installed'}); "
            "assert not lib.is_connected(); "
            "assert lib.connect()['connected']; "
            "assert lib.measure_temperature()==25.0; "
            "lib.safe_shutdown(); lib.disconnect()"
        )
        subprocess.run([str(python), "-c", code], cwd=environment, check=True)
    finally:
        shutil.rmtree(environment, ignore_errors=True)


def test_summary() -> tuple[int, float]:
    xml_path = ROOT / "release/pytest-junit.xml"
    root = ElementTree.parse(xml_path).getroot()
    if root.tag == "testsuite":
        tests = int(root.attrib.get("tests", 0))
    else:
        tests = sum(int(suite.attrib.get("tests", 0)) for suite in root.findall("testsuite"))
    coverage_path = ROOT / "release/coverage.json"
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    percent = float(coverage["totals"]["percent_covered"])
    return tests, percent


def write_release_metadata(wheel: Path, sdist: Path) -> None:
    release = ROOT / "release"
    api = yaml.safe_load((ROOT / "api/public_api.yaml").read_text(encoding="utf-8"))
    vectors = yaml.safe_load(
        (ROOT / "tests/conformance/data/protocol_vectors.yaml").read_text(encoding="utf-8")
    )["vectors"]
    tests, coverage = test_summary()

    files = sorted(path for path in ROOT.rglob("*") if included(path) and release not in path.parents)
    records = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "size": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in files
    ]
    manifest = {
        "schema_version": "1.0",
        "driver": NAME,
        "release_version": RELEASE_VERSION,
        "release_label": RELEASE_LABEL,
        "python_distribution": "rf-votsch-climate-chamber",
        "python_version": PEP440_VERSION,
        "api_version": API_VERSION,
        "release_class": RELEASE_CLASS,
        "d1_candidate": True,
        "fixed_root": NAME,
        "rfds_baseline": {
            "RFDS-001": "1.2",
            "RFDS-002": "1.1",
            "RFDS-003": "2.0",
            "RFDS-004": "2.0",
            "RFDS-005": "1.3",
            "RFDS-006": "1.0",
            "RFDS-007": "1.0",
            "RFDS-009": "1.0",
            "RFDS-010": "1.0",
            "RFDS-014": "1.0",
            "RFDS-015": "1.0",
            "RFDS-017": "3.0",
            "RFDS-018": "1.0",
            "RFDS-019": "1.1",
        },
        "validation": {
            "python_tests": "PASS",
            "python_test_count": tests,
            "coverage_percent": round(coverage, 2),
            "python_simulator_smoke": "PASS",
            "robot_dispatch_equivalent_conformance": "PASS",
            "robot_runtime_conformance": "NOT_RUN",
            "real_hardware": "NOT_RUN",
            "clean_install": "PASS",
            "wheel_install": "PASS",
            "ruff": "NOT_RUN",
            "mypy": "NOT_RUN",
            "libdoc": "NOT_RUN",
        },
        "public_keyword_count": len(api["keywords"]),
        "protocol_vector_count": len(vectors),
        "open_deviations": ["DEV-26.04-001"],
        "accepted_breaking_deviations": ["DEV-26.07-001"],
        "artifacts": {
            "wheel": wheel.relative_to(ROOT).as_posix(),
            "source_distribution": sdist.relative_to(ROOT).as_posix(),
        },
        "file_count": len(records),
        "files": records,
    }
    (release / "release_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (release / "release_manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
    )

    sbom = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"{NAME}-{RELEASE_VERSION}",
        "documentNamespace": f"https://example.invalid/spdx/{NAME}/{RELEASE_VERSION}",
        "creationInfo": {"creators": ["Tool: scripts/build_release.py"]},
        "packages": [
            {
                "name": "rf-votsch-climate-chamber",
                "SPDXID": "SPDXRef-Package",
                "versionInfo": PEP440_VERSION,
                "downloadLocation": "NOASSERTION",
                "licenseConcluded": "MIT",
            },
            {
                "name": "robotframework",
                "SPDXID": "SPDXRef-RobotFramework",
                "versionInfo": ">=7,<9",
                "downloadLocation": "https://pypi.org/project/robotframework/",
                "licenseConcluded": "Apache-2.0",
            },
            {
                "name": "jsonschema",
                "SPDXID": "SPDXRef-jsonschema",
                "versionInfo": ">=4.20,<5",
                "downloadLocation": "https://pypi.org/project/jsonschema/",
                "licenseConcluded": "MIT",
            },
        ],
    }
    (release / "sbom.spdx.json").write_text(json.dumps(sbom, indent=2) + "\n", encoding="utf-8")

    compatibility = {
        "release": RELEASE_VERSION,
        "api_version": API_VERSION,
        "python": ["3.11", "3.12", "3.13"],
        "robot_framework": ">=7,<9",
        "operating_systems": ["Windows", "Linux"],
        "real_device_models": "UNKNOWN",
        "simulator": "PASS",
        "legacy_robot_api": "REMOVED",
        "legacy_python_package": "REMOVED",
        "migration": "docs/migration.md",
    }
    (release / "compatibility_report.json").write_text(
        json.dumps(compatibility, indent=2) + "\n", encoding="utf-8"
    )

    trace_rows = [
        ["RFDS-002", "APPLICABLE", "rf_votsch_climate_chamber/library.py", "tests/api/test_metadata_consistency.py", "PASS", "review/v26.08_file_by_file_review.md", "DEV-26.07-001"],
        ["RFDS-003", "APPLICABLE", "rf_votsch_climate_chamber/lifecycle.py", "tests/unit/test_converters_errors_transport.py", "DEVIATION", "review/known_risks.md", "DEV-26.04-001"],
        ["RFDS-004", "APPLICABLE", "rf_votsch_climate_chamber/transports", "tests/integration/test_tcp_fake_server.py", "PASS", "review/v26.08_code_review.md", ""],
        ["RFDS-019", "APPLICABLE", "tests/conformance", "tests/unit/test_rfds_conformance_harness.py", "PASS_SIMULATOR", "review/v26.08_code_review.md", ""],
    ]
    with (release / "requirements_traceability.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["requirement_id", "applicability", "implementation", "verification", "result", "evidence", "deviation_id"])
        writer.writerows(trace_rows)

    validation = {
        "release": RELEASE_VERSION,
        "status": "D0_ACCEPTED_D1_CANDIDATE",
        "tests": tests,
        "coverage_percent": round(coverage, 2),
        "static_keyword_inventory": f"{len(api['keywords'])}/{len(api['keywords'])}",
        "protocol_vectors": len(vectors),
        "robot_runtime": "NOT_RUN",
        "hardware": "NOT_RUN",
        "clean_install": "PASS",
        "wheel_install": "PASS",
    }
    (release / "validation_report.json").write_text(
        json.dumps(validation, indent=2) + "\n", encoding="utf-8"
    )

    all_files = sorted(
        path
        for path in ROOT.rglob("*")
        if included(path) and path.name not in {"SHA256SUMS", "checksums.sha256"}
    )
    checksum_text = "".join(
        f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}\n" for path in all_files
    )
    (release / "SHA256SUMS").write_text(checksum_text, encoding="utf-8")
    (release / "checksums.sha256").write_text(checksum_text, encoding="utf-8")


def build_zip() -> tuple[Path, Path]:
    output = ROOT.parent / f"{NAME}_{RELEASE_LABEL}.zip"
    checksum = ROOT.parent / f"{NAME}_{RELEASE_LABEL}_SHA256SUMS.txt"
    output.unlink(missing_ok=True)
    files = sorted(path for path in ROOT.rglob("*") if included(path))
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive.write(path, (Path(NAME) / path.relative_to(ROOT)).as_posix())
    digest = sha256(output)
    checksum.write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    with zipfile.ZipFile(output) as archive:
        roots = {Path(name).parts[0] for name in archive.namelist()}
        assert roots == {NAME}
    print(f"Created {output} with {len(files)} files\nSHA-256 {digest}")
    return output, checksum


def main() -> int:
    if ROOT.name != NAME:
        raise SystemExit(f"fixed root must be {NAME}")
    clean_generated_outputs()
    run(sys.executable, "scripts/generate_rfds_metadata.py")
    shutil.copyfile(ROOT / "ai/votsch_climate_chamber_ai_contract.yaml", ROOT / "rf_votsch_climate_chamber/resources/votsch_climate_chamber_ai_contract.yaml")
    shutil.copyfile(ROOT / "ai/votsch_climate_chamber_ai_contract.lock", ROOT / "rf_votsch_climate_chamber/resources/votsch_climate_chamber_ai_contract.lock")
    run(sys.executable, "scripts/validate_structure.py")
    run(sys.executable, "scripts/validate_ai_contract.py")
    run(sys.executable, "scripts/validate_call_protocol_conformance.py")
    run(sys.executable, "-m", "compileall", "-q", "rf_votsch_climate_chamber", "tests", "scripts")
    run(
        sys.executable,
        "-m",
        "pytest",
        "--cov=rf_votsch_climate_chamber",
        "--cov-branch",
        "--cov-report=json:release/coverage.json",
        "--junitxml=release/pytest-junit.xml",
        "-q",
    )
    run(sys.executable, "scripts/run_python_simulator_smoke.py")
    wheel, sdist = build_distributions()
    clean_install_smoke(wheel)
    write_release_metadata(wheel, sdist)
    build_zip()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
