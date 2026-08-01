"""Verify wheel/sdist contents and test imports from the built wheel."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

EXPECTED_DISTRIBUTION_VERSION = "26.4.0"
EXPECTED_ROBOT_VERSION = "26.04"
EXPECTED_DRIVER_VERSION = "0.1.0"


def run(*args: str, cwd: Path, pythonpath: Path | None = None) -> None:
    env = os.environ.copy()
    if pythonpath is not None:
        env["PYTHONPATH"] = str(pythonpath)
    subprocess.run(args, cwd=cwd, env=env, check=True)


def find_artifact(dist: Path, suffix: str) -> Path:
    matches = sorted(dist.glob(f"robotframework_bk8500b-*{suffix}"))
    if not matches:
        matches = sorted(dist.glob(f"robotframework-bk8500b-*{suffix}"))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one *{suffix} artifact, found: {matches}")
    return matches[0]


def verify_metadata(wheel: Path, sdist: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        metadata_name = next((name for name in names if name.endswith(".dist-info/METADATA")), None)
        if metadata_name is None:
            raise RuntimeError("Wheel has no METADATA file")
        metadata = archive.read(metadata_name).decode("utf-8")
        for required in (
            "Name: robotframework-bk8500b",
            f"Version: {EXPECTED_DISTRIBUTION_VERSION}",
            "Requires-Python: >=3.10",
            "Requires-Dist: robotframework",
        ):
            if required not in metadata:
                raise RuntimeError(f"Wheel metadata missing {required!r}")
        for required_package in ("BK8500BLibrary/__init__.py", "bk8500b/__init__.py"):
            if required_package not in names:
                raise RuntimeError(f"Wheel missing {required_package}")
        if not any(name.endswith(".dist-info/licenses/LICENSE") for name in names):
            raise RuntimeError("Wheel does not contain the license")
        required_data_files = (
            "/share/rf_bk8500b/ai/bk8500b_ai_contract.yaml",
            "/share/rf_bk8500b/ai/bk8500b_ai_contract.lock",
            "/share/rf_bk8500b/ai/rfds017.schema.json",
            "/share/rf_bk8500b/bench/system_ai_contract.yaml",
        )
        for suffix in required_data_files:
            if not any(name.endswith(suffix) for name in names):
                raise RuntimeError(f"Wheel missing AI/bench resource {suffix}")

    with tarfile.open(sdist, "r:gz") as archive:
        names = set(archive.getnames())
        required_suffixes = (
            "/README.md",
            "/LICENSE",
            "/VERSION",
            "/release.json",
            "/history/v26.04.md",
            "/review/v26.04_ai_contract_review.md",
            "/review/rfds017_rfds018_traceability.md",
            "/guide/PYCHARM_SETUP.md",
            "/docs/index.html",
            "/examples/10_diagnostics_and_raw_scpi.robot",
            "/scripts/build_release.py",
            "/scripts/verify_ai_contract.py",
            "/ai/bk8500b_ai_contract.yaml",
            "/ai/bk8500b_ai_contract.lock",
            "/ai/rfds017.schema.json",
            "/bench/system_ai_contract.yaml",
            "/docs/AI_CONTRACT.md",
            "/docs/RFDS018_BENCH_TEMPLATE.md",
        )
        for suffix in required_suffixes:
            if not any(name.endswith(suffix) for name in names):
                raise RuntimeError(f"Source distribution missing {suffix}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--tests", type=Path, default=Path("tests"))
    args = parser.parse_args()
    dist = args.dist.resolve()
    tests = args.tests.resolve()
    wheel = find_artifact(dist, ".whl")
    sdist = find_artifact(dist, ".tar.gz")
    verify_metadata(wheel, sdist)

    with tempfile.TemporaryDirectory(prefix="rf-bk8500b-artifact-check-") as raw:
        temp = Path(raw)
        installed = temp / "installed"
        run(
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--no-index",
            "--target",
            str(installed),
            str(wheel),
            cwd=temp,
        )
        version_check = (
            "import BK8500BLibrary, bk8500b; "
            f"assert BK8500BLibrary.__version__ == '{EXPECTED_ROBOT_VERSION}'; "
            f"assert bk8500b.__version__ == '{EXPECTED_DRIVER_VERSION}'"
        )
        run(sys.executable, "-c", version_check, cwd=temp, pythonpath=installed)
        run(sys.executable, "-m", "bk8500b", "--help", cwd=temp, pythonpath=installed)
        run(
            sys.executable,
            "-m",
            "robot.libdoc",
            "BK8500BLibrary",
            "list",
            cwd=temp,
            pythonpath=installed,
        )

        copied_tests = temp / "tests"
        shutil.copytree(tests, copied_tests)
        run(
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--disable-warnings",
            str(copied_tests),
            f"--ignore={copied_tests / 'test_ai_contract.py'}",
            cwd=temp,
            pythonpath=installed,
        )

        rebuilt = temp / "rebuilt"
        rebuilt.mkdir()
        run(
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--no-index",
            "--no-build-isolation",
            "-w",
            str(rebuilt),
            str(sdist),
            cwd=temp,
        )
        if not list(rebuilt.glob("robotframework_bk8500b-*.whl")):
            raise RuntimeError("Could not rebuild a wheel from the source distribution")

    print("Release artifacts verified successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
