# Source Verification Record — Keysight 34970A/34972A Command Reference

**Source:** `Keysight_34970A_34972A_Command_Reference.md` (15,956 lines, Keysight version 2.00, 2009–2014)
**Stored verbatim:** MD5 `d0b9e4a2297f453c0c55a124c85acd4a`
**Verification date:** 2026-08-18
**Resolves:** every `SOURCE_VERIFICATION_REQUIRED` item and open questions 3, 4, 11–15 in spec v1.4

Each row below was checked against the command reference directly. Line numbers refer to the stored
copy.

---

## 1. Open questions resolved

### OQ-3 / OQ-4 — Continuity and diode measurement → `NOT_APPLICABLE`

Searched the full reference for `continuity` and `diode`, case-insensitive: **zero occurrences.**

Neither function exists on this instrument family. The prediction recorded in `DEEP_REVIEW_v1.1.md`
N4 is confirmed. Spec §11.2's `UNKNOWN` disposition becomes `NOT_APPLICABLE`, and its prohibition on
substituting resistance or voltage measurements stands — there is nothing to substitute *for*.

### OQ-11 — Monitor mode → `PUBLIC` (capability confirmed)

`ROUTe:MONitor` exists (line 6342), with a full command group:

```text
ROUTe:MONitor
ROUTe:MONitor?
ROUTe:MONitor:DATA?
ROUTe:MONitor:STATe
ROUTe:MONitor:STATe?
```

Monitor mode continuously reads one channel independently of the scan list. Alarms are evaluated
"during a scan **or a monitor measurement**" (lines 1468, 1603), confirming monitor and scan are
distinct acquisition modes that both consume the internal DMM — so the §5.2 locking model and the
§4.4 DMM gate both apply to it.

### OQ-12 — Card topology, current channels, four-wire pairing → all resolved

**Topology classes** (line 4176 ff.):

| Card | Description in reference | Topology class |
|---|---|---|
| 34901A | 20 Channel Multiplexer (2/4-wire), channels 21–22 current | multiplexer |
| 34902A | 16 Channel Multiplexer | multiplexer |
| 34903A | 20 Channel **Actuator/GP Switch** | actuator |
| 34904A | **4 × 8 Two-Wire Matrix** | matrix |
| 34905A / 34906A | RF multiplexer | RF multiplexer |
| 34907A | Multifunction (DIO / totalizer / DAC) | non-switching |
| 34908A | 40 Channel Single-Ended Multiplexer | multiplexer |

**Current measurement** — restricted to **channels 21 and 22 of the 34901A** (lines 2623, 2646,
2650, 2718). No other module supports current measurement. Spec §11.3's
`SOURCE_VERIFICATION_REQUIRED` is resolved.

**Four-wire pairing** — "pairs channel n in Bank 1 with channel **n+10** (34901A) or **n+8**
(34902A) to provide source and measurement connections" (lines 2969, 3182, 6619, 6898, 8516).
Spec §14.1's required per-card offset is resolved.

**Matrix addressing** — "channel 234 represents the intersection of **row 3 and column 4**" on the
34904A (lines 6722, 6801). Confirms the spec's M3 finding: the matrix cannot be addressed as a flat
multiplexer channel and needs a crosspoint model.

### OQ-13 — DAC output range → **−12 V to +12 V, 0.001 V resolution**

`SOURce:VOLTage <voltage>,(@<ch_list>)` (line 11429): "A number of volts from **-12 to +12**, in
resolution of **0.001 V**." DAC channels are 04 and 05 of a 34907A slot — e.g. `@304`, `@305`
(line 11445 ff.), matching the §21 safety example.

Spec §16.4's pre-transmission range validation now has concrete bounds.

### OQ-14 — Concurrent scan sessions

Not directly addressed by the command reference, which describes a single control session. The scan
engine, reading memory, and internal DMM are single shared resources, and monitor mode contends with
scanning for the DMM. This remains a **driver-level policy decision** for §5.2 rather than a device
fact; recorded as still open, but now with the contention set identified.

### OQ-15 — `Preset Device` side effect → resolved, and more hazardous than assumed

The reference gives two state tables. Their **module hardware effects are identical**:

| Module | Factory Reset (`*RST`), line 15310 | Instrument Preset (`SYSTem:PRESet`), line 15374 |
|---|---|---|
| 34901A, 34902A, 34908A | All Channels Open | All Channels Open |
| 34903A, 34904A | All Channels Open | All Channels Open |
| 34905A, 34906A | Channels s11 and s21 Selected | Channels s11 and s21 Selected |
| 34907A | Both DIO Ports = Input, Totalizer Count = 0, **Both DACs = 0 VDC** | same |

**This strengthens finding C2.** The deep review claimed `Reset Device` "opens all channel relays".
The reference shows it also **zeroes both DACs and clears the totalizer count**, and that
`SYSTem:PRESet` does exactly the same to module hardware. Both keywords therefore violate §21's
"never blindly open or close every relay" *and* "never blindly zero every DAC" — the two rules the
plan states side by side.

Spec §9.1's `Preset Device` entry, which recorded its side effect as "to be established", is
resolved: it is not a lighter-weight alternative to `Reset Device` at the hardware level.

---

## 2. Findings confirmed against source

### B4 — `Get Digital Direction` → `NOT_APPLICABLE`

Searched for a digital direction query (`DIGital…DIRection`, `:DIRection`, `DIGital…MODE`): **no
such command exists.**

Direction *state* does exist — the reset tables show "Both DIO Ports = **Input**" — but it is not
queryable. The v1.2 disposition is therefore correct and final: the keyword is dropped, and
driver-side synthesis of a direction register remains prohibited.

### B3 — Internal DMM gate → confirmed, with the discovery mechanism named

`INSTrument:DMM` exists, and the reference repeatedly qualifies measurement commands with "(see
`INSTrument:DMM` command) or not installed in the mainframe" (lines 192, 333, 434, 687, 757).

This confirms the internal DMM is optional *and* that it can be disabled in software — the
"installed vs enabled" distinction spec §4.4 requires. `INSTrument:DMM?` is the discovery mechanism
§6 needs.

---

## 3. Still open

| Item | Status | Reason |
|---|---|---|
| OQ-8 — available HIL hardware | OPEN | Deployment fact, not a device fact |
| OQ-9 — firmware compatibility exceptions | OPEN | Requires the target units' firmware revisions |
| OQ-14 — concurrent scan policy | OPEN | Driver policy decision; contention set now identified |
| OQ-5 — read-only calibration diagnostics | OPEN | Policy decision; `CALibration?` exists but exposure is a project call |
| Relay cycle count read (§19) | OPEN | Policy decision |

**Scope of this claim (corrected in v1.7).** No device-behaviour question remains unresolved *for
the enumerated command set*. The v1.6 command inventory was incomplete — it listed 193 block titles
rather than the 347 commands the reference declares in its Syntax sections — so questions were never
asked about commands that were never listed. Re-verified against the expanded 347-command inventory;
the remaining items below are deployment facts or project policy, neither of which the command
reference can answer.
