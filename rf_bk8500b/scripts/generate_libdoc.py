"""Generate HTML keyword documentation with Robot Framework Libdoc."""
from pathlib import Path

from robot.libdoc import libdoc

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "BK8500BLibrary.html"

if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    rc = libdoc("BK8500BLibrary", str(OUTPUT), format="HTML")
    if rc:
        raise SystemExit(rc)
    print(f"Generated {OUTPUT}")
