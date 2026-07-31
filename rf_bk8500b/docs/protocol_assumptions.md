# Protocol assumptions and ambiguity register

| ID | Issue | Candidate behavior | Release treatment |
|---|---|---|---|
| A-001 | SCPI terminators absent | Configurable `LF` defaults | Validate on each model/firmware |
| A-002 | Data/stop bits absent | Configurable 8N1 default | Validate adapter/interface |
| A-003 | `*RCL` 0–9 versus `*SAV` 0–99 | Enforce asymmetric documented ranges | Test real slots |
| A-004 | `*PSC` wording ambiguous | Support Boolean set/query | HIL readback required |
| A-005 | `SSTATus` typo | Use canonical `STATus` | Verify command acceptance |
| A-006 | Missing/contradictory parameter tables | Reject guesses | Evidence per affected command |
| A-007 | Protection delay commands referenced but absent | Not implemented | Official source required |
| A-008 | Legacy checksum modulo implicit | Sum first 25 bytes modulo 256 | Capture validation |
| A-009 | One section says checksum byte 27 | Enforce 26-byte frame, checksum index 25 | Capture validation |
| A-010 | Address ranges conflict | Stable address 0–31; broadcast disabled | HIL/official clarification |
| A-011 | 16 V example conflicts | Mathematical 16000 counts | Golden HIL vector required |
| A-012 | List repeat `65535` appears in one byte | Unlimited repeat blocked | Field-width capture required |
| A-013 | Reserved ranges omit/overlap | Build only verified fields | Per-command capture |
| A-014 | D8H/89H typo | Provisional D8H/D9H catalog | HIL required |
| A-015 | Autotest command IDs conflict | Experimental only | HIL required |
| A-016 | Von length/scale unclear | Experimental only | HIL required |
| A-017 | Legacy return-code byte location unclear | Do not parse/claim stable writes | Critical blocker |
| A-018 | Advanced legacy scales absent | Codec-only or blocked | Per-field evidence |
| A-019 | Mixing SCPI/legacy undocumented | Prohibited within a session | Keep prohibition unless validated |
| A-020 | Converted Markdown corruption | Preserve source notes | Original PDF cross-check required |
| A-021 | Front-panel changes invalidate cache | Query before hazards; degrade after local/raw | HIL workflow test |
| A-022 | Maximum command rate absent | Configurable 20 ms default pacing | Determine by soak |
| A-023 | Cable loss while input ON unspecified | No fail-safe claim | Hardware safety required |
| A-024 | Model/firmware differences incomplete | Runtime capability model | Per-model matrix required |

An ambiguity is not resolved merely because code or tests using a fake transport pass.
