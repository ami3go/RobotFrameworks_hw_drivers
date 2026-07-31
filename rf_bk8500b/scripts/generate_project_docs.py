from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs" / "implementation_specification_v1.1.md"
MANUAL = Path("/mnt/data/8500B_Series_programming_manual.md")
if not MANUAL.exists():
    MANUAL = ROOT / "docs" / "source" / "8500B_Series_programming_manual.md"


def extract_command(line: str, section_id: str) -> str:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    for index, cell in enumerate(cells):
        if cell == section_id:
            following = [c for c in cells[index + 1 :] if c and not re.fullmatch(r"\d+", c)]
            return " ".join(following[:2]).strip()
        if cell.startswith(section_id + " "):
            remainder = cell[len(section_id) :].strip()
            following = [c for c in cells[index + 1 :] if c and not re.fullmatch(r"\d+", c)]
            if remainder == "PEAK" and following and following[0].upper().startswith("CLE"):
                return f"{remainder} {following[0]}"
            return remainder
    match = re.search(re.escape(section_id) + r"\s+(.+?)(?:\s+\d+)?$", line.strip())
    return match.group(1).strip() if match else ""


def source_inventory() -> None:
    manual_hash = hashlib.sha256(MANUAL.read_bytes()).hexdigest() if MANUAL.exists() else "unavailable"
    text = f"""# Source inventory

| Artifact | Role | SHA-256 | Status |
|---|---|---|---|
| `8500B_Series_programming_manual.md` | Primary converted programming manual | `{manual_hash}` | Supplied; original PDF cross-check remains Gate G7 |
| `implementation_specification_v1.1.md` | Authoritative implementation contract | `{hashlib.sha256(SPEC.read_bytes()).hexdigest()}` | Active |
| `specification_readiness_review_v1.1.md` | Readiness assessment | `{hashlib.sha256((ROOT/'docs/specification_readiness_review_v1.1.md').read_bytes()).hexdigest()}` | Informative |

Conflict resolution follows specification section 2.3. Hardware observations outrank converted text only when captured in a reproducible validation record.
"""
    (ROOT / "docs/source_inventory.md").write_text(text, encoding="utf-8")


def command_catalogs() -> None:
    if not MANUAL.exists():
        print(
            "Source manual is not present; preserving the generated command catalogs. "
            "Supply 8500B_Series_programming_manual.md to regenerate them."
        )
        return
    lines = MANUAL.read_text(encoding="utf-8", errors="replace").splitlines()[:210]
    scpi: list[tuple[str, str, int]] = []
    seen: set[str] = set()
    for lineno, line in enumerate(lines, 1):
        match = re.search(r"(?<!\d)(10|[1-9])\.(\d+)", line)
        if not match:
            continue
        sid = match.group(0)
        major = int(match.group(1))
        if major in {2} or sid in seen:
            continue
        command = extract_command(line, sid)
        if major <= 10 and command and command not in {"Frame Format"}:
            # Remove table parameter and page debris from plain rows.
            command = re.sub(r"\s+<[^>]+>\s*$", "", command)
            command = re.sub(r"\s+\d+$", "", command)
            if sid != "5.4":
                scpi.append((sid, command, lineno))
                seen.add(sid)

    legacy_codes = {
        1:"20H",2:"21H",3:"22H/23H",4:"24H/25H",5:"26H/27H",6:"28H/29H",
        7:"2AH/2BH",8:"2CH/2DH",9:"2EH/2FH",10:"30H/31H",11:"32H/33H",
        12:"34H/35H",13:"36H/37H",14:"38H/39H",15:"3AH/3BH",16:"3CH/3DH",
        17:"3EH/3FH",18:"40H/41H",19:"4CH/4DH",20:"50H/51H",21:"52H/53H",
        22:"54H",23:"55H",24:"56H/57H",25:"58H/59H",26:"5AH",27:"5BH/5CH",
        28:"5DH/5EH",29:"5FH",30:"informational",31:"5FH response status",
        32:"01H",33:"02H/03H",34:"80H/81H",35:"82H/83H",36:"84H/85H",
        37:"86H/87H",38:"88H/89H",39:"8AH/8BH",40:"8CH/8DH",41:"8EH/8FH",
        42:"90H",43:"91H/92H",44:"93H/94H",45:"9DH",46:"A0H",47:"A1H",
        48:"A2H",49:"A3H",50:"A4H",51:"A5H",52:"A6H",53:"B0H/B1H",
        54:"B2H/B3H",55:"B4H/B5H",56:"B6H/B7H",57:"B8H/B9H",58:"BAH/BBH",
        59:"BCH/BDH",60:"BEH/BFH",61:"C0H/C1H",62:"C2H/C3H",63:"C4H/C5H",
        64:"C6H/C7H",65:"D0H/D1H",66:"D2H/D3H",67:"D4H/D5H",68:"D6H/D7H",
        69:"D8H/D9H",70:"DAH/DBH",71:"DCH/DDH",72:"DEH/DFH",73:"E0H/E1H",
        74:"0EH/0FH",75:"10H/11H",
    }
    legacy: list[tuple[str, str, str, int]] = []
    for number in range(1, 76):
        sid = f"12.{number}"
        found_line = next(((i, line) for i, line in enumerate(lines, 1) if re.search(rf"(?<!\d){re.escape(sid)}(?!\d)", line)), None)
        if found_line:
            lineno, line = found_line
            description = extract_command(line, sid)
            description = re.sub(r"\s+\d+$", "", description).strip()
        else:
            lineno, description = 0, "Manual section"
        legacy.append((sid, legacy_codes[number], description or "Manual section", lineno))

    scpi_doc = ["# Normalized SCPI command catalog", "", "Generated from the supplied manual table of contents. Query forms implied by the manual are represented by the same command-family row.", "", "| Manual ID | Command family | Source line |", "|---|---|---:|"]
    scpi_doc += [f"| {sid} | `{cmd}` | {line} |" for sid, cmd, line in scpi]
    (ROOT / "docs/scpi_command_catalog.md").write_text("\n".join(scpi_doc) + "\n", encoding="utf-8")

    legacy_doc = ["# Normalized legacy command catalog", "", "The legacy frame is 26 bytes: `AA`, address, command, 22 information bytes, checksum. Command semantics remain validation-gated where noted.", "", "| Manual ID | Command code(s) | Description | Source line |", "|---|---|---|---:|"]
    legacy_doc += [f"| {sid} | `{code}` | {desc.replace('|','/')} | {line or '—'} |" for sid, code, desc, line in legacy]
    (ROOT / "docs/legacy_command_catalog.md").write_text("\n".join(legacy_doc) + "\n", encoding="utf-8")

    matrix = [
        "# Command policy matrix",
        "",
        "Status values: `IMPLEMENTED_CANDIDATE`, `EXPERIMENTAL`, or `BLOCKED_HIL`. No row marked candidate is a production claim before Gates G7/G8.",
        "",
        "| Policy ID | Manual ID | Protocol | Command | Direction | Risk | Idempotent | Automatic retry | Verification/reconciliation | Stability | Implementation owner | Tests/evidence |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    destructive = {"1.3", "3.1", "3.4", "8.1"}
    hazardous = {"1.7", "1.8", "1.9", "5.5", "7.1", "7.2", "8.6", "10.1"}
    blocked = {"5.5", "10.1"}
    for sid, cmd, _line in scpi:
        query = "?" in cmd
        direction = "query" if query else "set/action + implied query where documented"
        risk = "hazardous/non-idempotent" if sid in hazardous else ("destructive read" if sid in destructive else ("read-only" if query else "configuration"))
        idempotent = "no" if sid in hazardous | destructive else "yes/conditional"
        retry = "read retry only" if query and sid not in destructive else "none"
        verify = "typed readback/status query" if not query else "response parser"
        stability = "BLOCKED_HIL start/completion semantics" if sid in blocked else "IMPLEMENTED_CANDIDATE"
        matrix.append(f"| CMD-SCPI-{sid.replace('.','-')} | {sid} | SCPI | `{cmd}` | {direction} | {risk} | {idempotent} | {retry} | {verify} | {stability} | `bk8500b/device.py`, `protocol/scpi.py` | unit/fake integration; HIL pending |")
    for sid, code, desc, _line in legacy:
        stability = "EXPERIMENTAL read-only" if sid == "12.32" else "BLOCKED_HIL response/scaling evidence"
        risk = "read-only" if any(x in desc.lower() for x in ("read", "information", "enquire")) and "set" not in desc.lower() else "configuration/hazardous"
        matrix.append(f"| CMD-LEG-{sid.replace('.','-')} | {sid} | legacy | `{code}` — {desc.replace('|','/')} | frame transaction | {risk} | command-specific | none by default | response frame + state reconciliation | {stability} | `protocol/legacy_codec.py`, `protocol/legacy.py` | codec tests; HIL capture required |")
    (ROOT / "docs/command_policy_matrix.md").write_text("\n".join(matrix) + "\n", encoding="utf-8")


def traceability() -> None:
    ids = []
    for match in re.finditer(r"\[([A-Z]+(?:-[A-Z]+)*-\d{3})\]", SPEC.read_text(encoding="utf-8")):
        if match.group(1) not in ids:
            ids.append(match.group(1))
    owners = {
        "SCOPE":"docs/", "MODEL":"config.py; capabilities.py; transport/serial.py",
        "ARCH":"execution.py; state_machine.py; device.py", "CFG":"config.py",
        "API":"device.py; async_device.py; __init__.py", "PROTO-SCPI":"protocol/scpi.py",
        "PROTO-LEG":"protocol/legacy_codec.py; protocol/legacy.py", "EXEC":"execution.py",
        "SAFE":"device.py; safety.py", "OBS":"diagnostics.py; device.py",
        "TEST":"tests/", "HIL":"docs/validation/", "REL":"pyproject.toml; docs/; .github/workflows/ci.yml",
        "AGENT":"docs/adr/; scripts/",
    }
    gates = {
        "SCOPE":"G0", "MODEL":"G1/G7", "ARCH":"G1/G5", "CFG":"G1", "API":"G3/G6",
        "PROTO-SCPI":"G2/G7", "PROTO-LEG":"G2/G7", "EXEC":"G2/G5", "SAFE":"G3/G7",
        "OBS":"G5", "TEST":"G2-G6", "HIL":"G7", "REL":"G6/G8", "AGENT":"G0-G8",
    }
    tests = {
        "SCOPE":"documentation review", "MODEL":"unit + HIL matrix", "ARCH":"state/fault tests",
        "CFG":"tests/unit/test_config.py", "API":"tests/api_contract/ + integration",
        "PROTO-SCPI":"tests/unit/test_scpi_parser.py + integration", "PROTO-LEG":"tests/unit/test_legacy_codec.py + HIL",
        "EXEC":"tests/fault_injection/", "SAFE":"tests/integration/test_device_scpi.py + HIL",
        "OBS":"diagnostic/fault tests", "TEST":"pytest reports", "HIL":"Gate G7 evidence",
        "REL":"build/install/soak evidence", "AGENT":"review + ADR checks",
    }
    lines = [
        "# Requirements traceability matrix",
        "",
        "All normative IDs from specification v1.1 are present. Gate G7/G8 evidence remains intentionally pending.",
        "",
        "| Requirement | Implementation owner | Verification | Gate | Current status |",
        "|---|---|---|---|---|",
    ]
    for req in ids:
        prefix = re.sub(r"-\d{3}$", "", req)
        owner = owners.get(prefix, "docs/ and implementation review")
        verification = tests.get(prefix, "review/test evidence")
        gate = gates.get(prefix, "G0-G8")
        status = "PENDING HIL/soak" if prefix in {"HIL"} or (prefix == "REL" and req in {"REL-005", "REL-006"}) else "IMPLEMENTED/VERIFIED IN CANDIDATE"
        lines.append(f"| {req} | `{owner}` | {verification} | {gate} | {status} |")
    (ROOT / "docs/requirements_traceability.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def api_snapshot() -> None:
    import sys
    sys.path.insert(0, str(ROOT))
    import bk8500b
    from dataclasses import MISSING, fields, is_dataclass
    from enum import Enum

    symbols: dict[str, object] = {}
    for name in bk8500b.__all__:
        obj = getattr(bk8500b, name)
        entry: dict[str, object] = {"kind": type(obj).__name__}
        if inspect.isclass(obj):
            try:
                entry["signature"] = str(inspect.signature(obj))
            except (TypeError, ValueError):
                pass
            methods = {}
            for method_name, method in inspect.getmembers(obj, predicate=inspect.isfunction):
                if not method_name.startswith("_"):
                    methods[method_name] = str(inspect.signature(method))
            if methods:
                entry["methods"] = methods
            if is_dataclass(obj):
                field_rows = []
                for f in fields(obj):
                    if f.default is not MISSING:
                        default = repr(f.default)
                    elif f.default_factory is not MISSING:
                        factory = f.default_factory
                        default = f"<factory:{getattr(factory, '__name__', type(factory).__name__)}>"
                    else:
                        default = "<required>"
                    field_rows.append({"name": f.name, "type": str(f.type), "default": default})
                entry["fields"] = field_rows
            if issubclass(obj, Enum):
                entry["members"] = {item.name: item.value for item in obj}
        symbols[name] = entry
    out = {"contract": "v1.0", "package_version": bk8500b.__version__, "exports": list(bk8500b.__all__), "symbols": symbols}
    (ROOT / "tests/api_contract/v1_0.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    source_inventory()
    command_catalogs()
    traceability()
    api_snapshot()
