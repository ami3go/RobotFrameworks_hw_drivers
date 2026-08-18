# Deep Review — RF Keysight 349xx Driver Implementation Plan v1.1

> **STATUS: CLOSED — all findings resolved.** This review covers **v1.1**. Every finding below
> (C1–C3, M1–M12, X1–X5) was applied in **v1.2** across 24 verified edits; see the v1.2 revision
> history for the finding-to-section mapping, and section 9 of this document for per-finding
> disposition.
> **The current specification is `RF_Keysight349xx_Driver_Implementation_Plan_v1.2.md`.**
> Retained as the historical record — do not read the findings below as open.

**Reviewed document:** `RF_Keysight349xx_Driver_Implementation_Plan_v1.1.md`
**Review date:** 2026-08-18
**Predecessor review:** `SPEC_REVIEW.md` (reviewed v1.0; findings B1–B4 and N1–N8)
**Scope:** specification only — no implementation exists, and none was written for this review.

---

## 1. Verdict

**v1.1 correctly closes B1–B4. It is not yet ready to enter Phase 1 Gate 1.**

This pass went after a different class of problem than the v1.0 review: not structural gaps, but
**technical errors, safety contradictions, and requirements that are stated but never specified**.
It found three critical items and twelve major ones.

The three critical findings share a shape worth naming: in each case the plan states a strong safety
principle in one section and then contradicts it in another. §22.1 authorises retrying a destructive
read. §9 exposes a keyword that violates §21's central ownership rule. §18 exposes keywords that can
sever the connection carrying them. None is a drafting slip — each would produce a driver that is
unsafe on a shared bench while appearing to comply with its own safety model.

The plan's evidence-first discipline remains its strongest feature and is unaffected by these
findings.

---

## 2. Status of the v1.0 findings

| ID | Finding | v1.1 status |
|---|---|---|
| B1 | `src/` layout | **Resolved** — flat root; remaining `src/` mentions are prose explaining the decision |
| B2 | RFDS-008 absent | **Resolved** — §2.1.1 artifact contract, `evidence.py`, Gate 3/4 deliverables, RFDS-011/013/016 dispositions |
| B3 | Internal DMM not gated | **Resolved** — §4.4, §6, §11.1 |
| B4 | `Get Digital Direction` | **Resolved** — `UNKNOWN`, synthesis prohibited |
| N1, N2, N3, N5, N7, N8 | — | **Resolved** |
| N4, N6 | — | Deferred to `release/open_questions.yaml` as intended |

No regression was introduced by the v1.1 edits except **X1** below, which is fallout from the N7 fix.

---

## 3. Critical findings

### C1 — `SYST:ERR?` is a destructive read and must not be retried

**Where:** §22.1, which lists `SYST:ERR?` among operations "demonstrably safe and idempotent" and
therefore eligible for bounded retry.

**Problem:** Reading the SCPI error queue **removes** the error that is read. `SYST:ERR?` is not
idempotent. If the query is transmitted, the instrument pops and returns an error, and the response
is then lost to a timeout or a partial read, an automatic retry returns the *next* error — or
`0,"No error"`. The lost error is gone permanently.

This is exactly the failure mode §10 is designed to prevent. §10 requires the driver to "distinguish
no-error from malformed response" and to "never interpret malformed SCPI as `0,"No error"`", and
§22.1 then authorises a retry that can silently manufacture that same false clean state.

The consequence is worse than a lost diagnostic: the error queue is the mechanism by which the driver
learns that a *previous* state-changing command failed. Silently discarding a queue entry can mask a
failed relay or DAC write.

**Recommendation:** Remove `SYST:ERR?` from §22.1. Classify it explicitly as a destructive read with
`retry: PROHIBITED`. On timeout it shall surface the timeout, and the queue state shall be reported
as `UNKNOWN` rather than assumed. Add a third category to §22 for **destructive reads** — operations
that are read-only with respect to *device configuration* but state-changing with respect to
*device buffers*. `R?` and `DATA:REMove?` (§12) belong in the same category and are currently
unclassified for retry purposes.

### C2 — `Reset Device` contradicts the §21 ownership safety model

**Where:** §9 lists `Reset Device` and `Preset Device` as planned public keywords. §21 requires the
driver to "never blindly open or close every relay" and to "never assume exclusive ownership of
shared bench resources".

**Problem:** On these mainframes `*RST` opens all channel relays and returns the instrument to its
default state. A public `Reset Device` keyword therefore does precisely what §21 forbids — and it
does so in a single call, bypassing the entire ownership model, on a frame that may be carrying
another team's wiring.

The plan applies careful ownership reasoning to `Safe Shutdown` (§21) and to switching (§15.1), then
offers an unqualified keyword that overrides both.

**Recommendation:** This requires an explicit decision, not silent inclusion. Options, in order of
preference:

1. classify `Reset Device` / `Preset Device` as **high-risk, confirmation-gated** — requiring an
   explicit confirmation argument in the manner §19 applies to service operations;
2. gate them on the bench contract (§26) declaring whole-frame ownership;
3. exclude them, with the disposition recorded in the vendor coverage audit.

Whichever is chosen, §9 shall state the relay side effect explicitly, and the AI contract entry
(§25) shall record it as a state transition affecting **all** routing resources, owned or not.
`Clear Status` (`*CLS`) is unaffected — it touches only status registers — and should be documented
as the safe member of that group.

### C3 — 34972A LAN configuration keywords can sever the connection carrying them

**Where:** §18 lists LAN configuration, hostname, DHCP, IP address, gateway, and subnet mask as
potential 34972A capability families.

**Problem:** When the driver is connected over LAN — the primary 34972A transport per §30 — changing
the IP address, subnet mask, gateway, or DHCP mode destroys the connection executing the command.
The command may or may not have been applied before the link dropped, and the driver cannot query
the result, because the path it would query over no longer exists.

§22.2 already forbids blind retry where delivery is uncertain and mandates a query/compare/reconcile
recovery. For these specific commands **reconciliation is impossible over the affected transport**,
so the section's own recovery strategy cannot be executed.

The plan classifies them merely as "potential capability families" with no risk marking. §18's only
stated gate is model gating — that they exist on the 34972A and not the 34970A — which is orthogonal
to the hazard.

**Recommendation:** Split §18 into two groups with different dispositions:

```yaml
lan_query:                # hostname?, IP?, DHCP?, MAC?, LAN status
  status: PUBLIC
  risk: NONE              # read-only, no communication impact

lan_configuration:        # set IP, subnet, gateway, DHCP on/off, hostname
  status: EXCLUDED        # default disposition
  reason: >
    Changes the transport the command is delivered over; §22.2 reconciliation
    is impossible on the affected connection. Reconfiguration belongs to a
    separate provisioning procedure, not general automation.
```

If any write is later promoted to public, it shall be confirmation-gated, shall be documented as
terminating the session, and shall be prohibited when the active transport is the one being
reconfigured — that is, permitted over USB while changing LAN settings, but never over LAN.

---

## 4. Major findings

### M1 — Raw protocol I/O is listed as a capability group but never specified

§8 lists "raw protocol I/O" among the conditional RFDS capability groups. Nothing else in the
document defines it: no keyword names, no risk classification, no enable gate, no interaction with
§19's exclusions or §21's ownership model.

This is a significant hole. Raw SCPI is the universal bypass — with it, every exclusion in §19
(calibration writes, security changes, `DIAG:POKE`) and every safety rule in §21 becomes advisory,
because the caller can transmit the command directly. Another driver in this repository gates raw
SCPI behind an explicit enable keyword for exactly this reason.

**Recommendation:** Add a dedicated section specifying: the keyword set; a mandatory enable gate
(disabled by default, enabled only by an explicit keyword with a confirmation argument); a
high-risk classification; a requirement that raw traffic is captured in protocol evidence like any
other exchange; and an explicit statement that raw I/O does **not** exempt the caller from §19 or
§21, with that limitation stated in the AI contract.

### M2 — Contract synchronization is mandated with no tooling to enforce it

§25 requires the AI contract, capability model, public API inventory, and RFDS-019 protocol vectors
to "remain synchronized". §28 requires 100% keyword inventory coverage. §37 provides
`ai/ai_contract.lock` and `config/schema.lock`.

But §32's script list contains no generator or validator: `setup_env`, `run_unit_tests`,
`run_examples`, `run_conformance`, `build_docs`, `build_dist`, `validate_package`, `release_check`.
Nothing regenerates the metadata and nothing verifies the lock.

Synchronization requirements without tooling drift — reliably, and silently. Other drivers in this
repository carry both a metadata generator and a contract validator, and adding a keyword there
fails the build until the metadata is regenerated. That is the mechanism that makes §25 real.

**Recommendation:** Add `generate_metadata.{ps1,sh}` and `validate_ai_contract.{ps1,sh}` to §32, add
a metadata-synchronization check to §29.1, and make a stale lock a release-blocking failure in §53.

### M3 — Switching semantics conflate multiplexers with actuators and matrices

§15 specifies `Open Channel`, `Close Channel`, `Open Channels`, `Close Channels`, and `Get Channel
State` as if all supported cards behaved identically. They do not:

- **multiplexer** cards (34901A, 34902A, 34908A) are break-before-make within a bank — closing one
  channel opens the previously closed one, so `Close Channels` with several channels in the same
  bank is not physically satisfiable;
- **actuator/general-purpose** cards (34903A) have independent SPDT relays that can all be closed
  simultaneously;
- **matrix** cards (34904A) are addressed by row/column crosspoint, not a flat channel number;
- **RF multiplexer** cards (34905A/34906A) have their own switching topology.

A uniform `Close Channels` will therefore either silently fail or produce a state the caller did not
request, depending on which card is installed.

**Recommendation:** Make switching semantics card-class-aware. Validate multi-channel close requests
against the installed card's topology and reject same-bank multiplexer conflicts *before*
transmission, in keeping with §11.1's pre-transmission validation posture. Add a matrix addressing
model for the 34904A or exclude it explicitly. Confirm each card's topology against the command
reference and record it in the capability model.

### M4 — Write reconciliation needs bounded polling, not a single readback

§22.2's recovery strategy — "query state / compare expected state / recover or fail explicitly" — is
correct in structure but under-specified in timing. It does not say whether the query is a single
immediate read or a bounded poll.

This distinction has a concrete, recently demonstrated cost in this repository: a driver here
verified digital-output writes with one instantaneous readback and produced false safety failures on
real hardware, because the instrument acknowledged the write before its readback register reflected
it. The fix was a bounded poll against a deadline. The same driver had already learned this for
analog setpoints and simply had not applied it to the digital path.

The 34907A DAC and the routing relays in this plan are in exactly that category: mechanical and
analog settling time is real, and an immediate readback can legitimately disagree with a successful
write.

**Recommendation:** Specify reconciliation as a **bounded poll** with an explicit timeout and poll
interval, both configurable per §23, and require the timeout error to carry the requested value, the
last observed value, the attempt count, and elapsed time. State that a single instantaneous readback
is insufficient for relay and DAC verification.

### M5 — Simulator must not acknowledge writes it does not model

§27 lists the state the simulator shall emulate but does not state what happens when a command
addresses something outside that state — for example a routing channel, digital port, or DAC channel
the simulator does not model.

The failure mode is specific and has occurred in this repository: a simulator that accepts a write to
an unmodelled channel, returns success, and then reports the unchanged value on readback. Every
write-verify round trip against that channel fails forever, and the failure looks like a driver or
hardware bug rather than a simulator gap. It cost a real debugging cycle here.

**Recommendation:** Require the simulator to either model the addressed resource faithfully or reject
the command as an unsupported-command fault (§27.1 already defines that fault type). Acknowledging a
write that was not performed shall be explicitly prohibited. Add a conformance check that every
channel the capability model reports as available is actually modelled by the simulator.

### M6 — Session and resource locking is tested but never specified

§29.1 step 20 requires "resource-locking tests". §5's architecture diagram lists "locking" as a
`BaseInstrumentLibrary` responsibility. Nothing else in the document defines locking at all: not its
granularity, not its scope, not its behaviour under contention.

For this instrument the question is not academic. §8 requires multi-connection support, and a
mainframe is a genuinely shared resource — two sessions can address the same slot, the same relay,
or the same scan engine. A scan initiated by one session and fetched by another is a real hazard,
because `FETCh?` and `R?` consume shared reading memory.

**Recommendation:** Specify the locking model: what is locked (session, mainframe, scan engine,
per-slot resources), lock granularity, acquisition and timeout behaviour, and what happens when a
second session attempts an operation on a locked resource. Address explicitly whether concurrent
scan operations from different sessions are permitted or refused.

### M7 — Safe shutdown behaviour with no declared ownership is ambiguous

§21 requires ownership-aware safe shutdown and instructs the driver to "fail closed when required
safety information is unknown". The example configuration declares owned channels, ports, and DAC
outputs. What §21 does not state is the behaviour when **no ownership is configured at all** — the
default for a fresh installation, since §23.1 requires defaults to contain no bench-specific data.

"Fail closed" is ambiguous here. It could mean refuse to run, do nothing, or act on everything —
and the last reading is the dangerous one.

**Recommendation:** State it explicitly. The recommended behaviour, consistent with §21's own
principles and with the precedent in this repository, is: abort any active scan (§21 already
requires this unconditionally), report every ownership-dependent action as `SKIP` with a reason, and
return an overall result that is honest about what was and was not placed in a safe state — never
silently claiming a safe state it did not establish. Require the per-action outcome list in the
return value so callers can assert on it.

### M8 — Current measurement channel restriction is not stated

§11 lists `Measure DC Current` and `Measure AC Current`. §11.1 requires validating "installed card
compatibility" generically, but the plan never records the actual restriction: on these mainframes
current measurement is available only on specific dedicated current channels of the 34901A, and is
not available on the other multiplexer cards at all.

Left generic, this becomes a runtime device error rather than the pre-transmission
`DriverUnsupportedOperationError` §11.1 promises.

**Recommendation:** Record the per-card current-capable channel set in the capability model, verify
it against the command reference, and validate before transmission.

### M9 — Four-wire pairing rule is required but not stated

§14.1 requires the implementation to "understand four-wire pairing rules for supported cards rather
than treating all channel numbers as independent" — correct and important — but never states the
rule, and it is card-dependent (the source and paired channel are separated by a fixed offset that
differs between the 34901A and 34902A). Four-wire operation also halves the usable channel count on
a card, which affects channel enumeration in §15.

**Recommendation:** Record the pairing offset per card in the capability model as sourced data,
verify against the command reference, and state that `List Switch Channels` and channel validation
must reflect the reduced channel set when a four-wire function is configured.

### M10 — Monitor mode is entirely absent

The document contains no reference to monitor mode (`ROUT:MON`), a significant capability of these
mainframes that continuously reads a single channel independently of the scan list.

Given §1's requirement that every capability be traceable and that anything unestablished be marked
`UNKNOWN`, `NOT_APPLICABLE`, or `EXCLUDED`, a whole feature family with no disposition is a gap in
the audit rather than an omission of scope.

**Recommendation:** Give monitor mode an explicit disposition in §20's vendor command coverage
audit. Note that it interacts with the scan engine and with the locking model (M6), since monitor
mode and an active scan contend for the internal DMM.

### M11 — Error queue drain is "bounded" with no bound

§10 requires "complete queue draining with bounded iteration" but specifies neither the bound nor
the behaviour on reaching it. A driver that stops draining at an unspecified limit and reports the
queue as empty would violate §10's own honesty requirement.

**Recommendation:** Specify the maximum drain iterations, and require that hitting the bound is
reported as an explicit `UNKNOWN`/truncated result rather than a successfully emptied queue.

### M12 — Recovery is required but no recovery keyword is defined

§28.1 requires a "recovery vector" for every keyword and §29.1 step 15 requires recovery tests.
§48 lists "session recovery" as a Phase 10 deliverable. But §7's mandatory keyword list contains no
reconnect or recover keyword, and §8's conditional groups do not name one either.

**Recommendation:** Define the recovery keyword explicitly in §7 or §8 — including whether it
preserves session configuration, what it does to an active scan, and how it interacts with the
ownership model — so the recovery vectors required by §28.1 have a subject.

---

## 5. Consistency findings

| ID | Finding | Location |
|---|---|---|
| X1 | Definition of Done still requires "at least ten examples exist" while §31 now fixes the target at fifteen. Direct fallout of the v1.1 N7 fix; the two must agree or the acceptance check is ambiguous. | §53 vs §31 |
| X2 | §29.1's 22-step verification sequence gained no evidence-completeness step when RFDS-008 entered scope in v1.1. Add one covering run finalization and derived `final_status` (§2.1.1). | §29.1 vs §2.1.1 |
| X3 | The HIL matrix has no DMM-present / DMM-absent dimension, although v1.1 made internal-DMM availability a first-class capability gate. A switch-only frame is a distinct qualification target. | §30 vs §4.4 |
| X4 | Configuration examples cover simulator, 34970A GPIB, 34970A RS-232, and 34972A LAN — but §30 also lists 34972A USB/VISA as a qualified transport, with no matching example. | §23 vs §30 |
| X5 | §16.4 specifies DAC keywords and §21 gives DAC safe values, but nothing requires validation of the DAC output range before transmission. Given §21's fail-closed posture and the DAC's classification as safety-relevant, range validation should be an explicit pre-transmission check. | §16.4, §21 |

---

## 6. Scoring

| Area | Weight | v1.0 | v1.1 | Note |
|---|---:|---:|---:|---|
| Scope and objective | 10% | 9.5 | 9.5 | unchanged |
| Architecture and layering | 10% | 8.0 | 9.5 | B1 resolved |
| Safety model | 20% | 9.8 | 7.0 | C1, C2, C3, M1, M7 — principles stated then contradicted |
| API completeness and capability gating | 15% | 8.0 | 8.0 | B3 resolved; M1, M3, M12 offset the gain |
| Device-technical accuracy | 10% | — | 6.5 | new axis: C1, M3, M8, M9, M10 |
| Test and conformance strategy | 15% | 9.7 | 8.5 | M2, M5, M6 |
| Hardware qualification boundary | 10% | 9.6 | 9.3 | X3 |
| Packaging and repository fit | 5% | 6.0 | 9.5 | B1 resolved |
| Evidence and traceability | 5% | 8.5 | 9.5 | B2 resolved |

**Overall: 8.16 / 10** (v1.0 scored 8.96 on a coarser rubric).

The score moves down despite four blockers being resolved, because this pass examined device
semantics and safety-model coherence — dimensions the first review did not probe. The drop is a
change in measurement, not a regression in the document.

---

## 7. Required actions before Phase 1 Gate 1

**Blocking:**

1. **C1** — remove `SYST:ERR?` from retry-eligible operations; add a destructive-read category
   covering `SYST:ERR?`, `R?`, and `DATA:REMove?`.
2. **C2** — decide and record the disposition of `Reset Device` / `Preset Device` against §21.
3. **C3** — split §18 into LAN query (public) and LAN configuration (excluded by default).
4. **M1** — specify raw protocol I/O, including its enable gate and its non-exemption from §19/§21.
5. **M2** — add metadata generation and contract validation to §32 and §29.1.
6. **X1** — reconcile the example count between §31 and §53.

**Before their respective phases:**

7. **M3, M8, M9, M10** — source-verify card topologies, current-channel restrictions, four-wire
   pairing offsets, and monitor mode against the command reference; record all four in the
   capability model and vendor coverage audit. *(Phases 3, 5, 6)*
8. **M4, M5** — specify bounded-poll reconciliation and prohibit simulator acknowledgement of
   unmodelled writes. *(Phases 1, 7)*
9. **M6, M7, M11, M12** — specify locking, no-ownership safe-shutdown behaviour, the error-queue
   bound, and the recovery keyword. *(Phases 1, 2, 10)*
10. **X2–X5** — consistency repairs.

Items 1–6 are document edits only. Items 7 requires the Keysight command reference, which is listed
in §2.2 as an authoritative source but was not available to this review — every device-technical
claim in §4 above is therefore flagged for source confirmation rather than asserted as established.

---

## 8. Status

```text
Reviewed:               RF_Keysight349xx_Driver_Implementation_Plan_v1.1.md
Implementation:         NOT STARTED — no code written
v1.0 findings:          B1-B4 resolved, N1/N2/N3/N5/N7/N8 resolved, N4/N6 deferred as intended
New critical findings:  3  (C1-C3)   — all resolved in v1.2
New major findings:     12 (M1-M12)  — all resolved in v1.2
New consistency issues: 5  (X1-X5)   — all resolved in v1.2
Current specification:  RF_Keysight349xx_Driver_Implementation_Plan_v1.2.md
Next step:              Phase 1 Gate 1, once the command reference closes the
                        SOURCE_VERIFICATION_REQUIRED items
```

---

## 9. Disposition in v1.2

| ID | Resolution in v1.2 | Section |
|---|---|---|
| C1 | Destructive-read category added; retry prohibited for `SYST:ERR?`, `R?`, `DATA:REMove?`; §22.1 narrowed to operations changing no buffer or queue state | §22.1, §22.3 |
| C2 | `Reset Device` / `Preset Device` reclassified high-risk and confirmation-gated; all-relay side effect stated; `Clear Status` documented as the safe member | §9.1 |
| C3 | LAN family split into `lan_query: PUBLIC` and `lan_configuration: EXCLUDED`; any future promotion forbidden over the transport being reconfigured | §18.1, §18.2 |
| M1 | Raw protocol I/O fully specified: default-disabled enable gate, risk classes, evidence capture, no exemption from §19/§21, no internal use | §8.1 |
| M2 | `generate_metadata` and `validate_ai_contract` added; stale lock is release-blocking | §32, §32.1, §29.1, §53 |
| M3 | Card-class-aware switching required; four topology classes named; same-bank multiplexer conflicts rejected pre-transmission; matrix needs a crosspoint model or exclusion | §15.2 |
| M4 | Reconciliation is a bounded poll with configurable timeout and interval; error carries requested, observed, attempts, elapsed | §22.2 |
| M5 | Simulator must model or reject; acknowledging an unperformed write prohibited; conformance check ties simulator coverage to the capability model | §27.2 |
| M6 | Locking model specified: granularity, acquisition, contention, scan exclusivity, release on failure; never silently advisory | §5.2 |
| M7 | No-ownership safe shutdown defined: abort scan, `SKIP` every ownership-dependent action with a reason, per-action outcome list, never claim an unachieved safe state | §21.2 |
| M8 | Current-capable channel set per card made a `SOURCE_VERIFICATION_REQUIRED` capability-model field with pre-transmission enforcement | §11.3 |
| M9 | Four-wire pairing offset and reduced channel set made per-card sourced data affecting channel enumeration | §14.1 |
| M10 | Monitor mode added as a required disposition; DMM contention with the scan engine noted | §12.1, §54 |
| M11 | Drain bound configurable; truncation reported explicitly; `Device Error Queue Should Be Empty` fails on truncation | §10.2 |
| M12 | `Recover Connection` defined, including scan abort and the prohibition on re-applying owned safe states | §8.2 |
| X1 | Definition of Done reconciled to fifteen examples | §53 |
| X2 | Evidence-completeness and metadata-synchronization steps added to the verification sequence | §29.1 |
| X3 | DMM-present / DMM-absent dimension added to the HIL matrix | §30.4 |
| X4 | `34972a_usb.json` added; one config example required per qualified transport | §23 |
| X5 | DAC range validation required pre-transmission; unknown range blocks writes | §16.4 |

**Not resolved by document edit, by design.** M3, M8, M9, M10 and the DAC range in X5 are recorded
as `SOURCE_VERIFICATION_REQUIRED` rather than answered, and carried as open questions 11–15. The
Keysight command reference was unavailable to this review; §1 forbids resolving device behaviour by
assumption, so recording the requirement is the correct resolution and answering it from memory
would not have been.
