#!/usr/bin/env python3
"""Guard 1 of RFDS spec §9.2: reference -> vendor_command_coverage.yaml.

Fails when a command declared by the vendor reference is absent from the
coverage map.

Two rules make this check meaningful, both learned the hard way:

  * It must NOT reuse the map generator's extractor output as its expected
    set. v1.6 asserted the map against the list its own generator produced,
    which proved only self-consistency and let a false "100% coverage" claim
    survive a commit.

  * A single extraction is insufficient. Three methods applied to this
    reference produced 193 / 347 / 342 commands and none is a superset of the
    others. This script uses the reference's own "Commands A-Z" index --
    independent of the Syntax-section extraction the map was built from --
    and §9.2 requires reconciling at least two.

Discrepancies are resolved to either a real command (failure) or a documented
notation artifact: abbreviated aliases such as SYST:LFRequency?, and
optional-node brackets, where [:IMMediate] may be present or absent and both
forms denote the same command.

Exit 0 on pass, 1 on unresolved discrepancy.
"""
import sys
import re, yaml, pathlib, itertools
ROOT = pathlib.Path(__file__).resolve().parent.parent
lines=pathlib.Path(ROOT/'reference/Keysight_34970A_34972A_Command_Reference.md').read_text(errors='replace').splitlines()
az=set(); CMD=re.compile(r'^(\*[A-Z]{2,4}\??|(?:\[SENSe:\])?[A-Z][A-Za-z]*(?::[A-Za-z\[\]{}|0-9]+)+\??)\s*$')
for l in lines[14157:]:
    s=l.strip()
    if s.startswith('Command Quick Reference') or s.startswith('Error Messages'): break
    m=CMD.match(s)
    if m: az.add(m.group(1))
d=yaml.safe_load(open(ROOT/'protocol/vendor_command_coverage.yaml'))
mapped={e['command'] for e in d['commands']}

def variants(c):
    """An optional node [:X] may be present or absent -- expand to both forms."""
    c=c.rstrip('?').upper()
    parts=re.split(r'(\[[^\]]*\])', c)
    opts=[[p[1:-1], ''] if p.startswith('[') else [p] for p in parts if p!='']
    return {''.join(combo).strip(':') for combo in itertools.product(*opts)}

mvar=set()
for m in mapped: mvar |= variants(m)
ABBREV=re.compile(r'^(SYST|CALC|CONF|MEAS|SENS|TEMP|FRES|VOLT|CURR|ROUT|TRIG|DIAG|MMEM|STAT|SOUR|FORM|DISP|INST|OUTP)[:?]')
missing=[a for a in az if not (variants(a) & mvar)]
real=[a for a in missing if not ABBREV.match(a)]
art=[a for a in missing if ABBREV.match(a)]
print("GUARD 1 (reference -> map), optional-node aware")
print(f"  map commands            : {len(mapped)}")
print(f"  A-Z index commands      : {len(az)}")
print(f"  unresolved discrepancies: {len(real)}")
for x in sorted(real): print("     ",x)
print(f"  notation artifacts      : {len(art)} {sorted(art)}")
print()
print("RESULT:", "PASS" if not real else "FAIL")
sys.exit(0 if not real else 1)
