# Phase 1, Gate 5 — Code review record

Reviewed: `bk8500_load` v26.01.04. Resolutions delivered in **v26.01.05**.
Method: adversarial self-review of the driver, with each suspicion tested
against the code rather than judged by inspection.

## Findings and resolutions

| ID | Severity | Finding | Resolution in v26.01.05 | Regression test |
|----|----------|---------|-------------------------|-----------------|
| R-1 | Critical | `_query` required the reply's command byte to echo the request. The manual never states this for read commands and the vendor's own examples never check byte 2. Firmware that tags replies `0x12` would fail **every** read keyword | Both framings accepted; the style is detected, logged once and reported as `response_style`. A `0x12` reply carrying status `0x80` and no payload is genuinely ambiguous and raises rather than returning `0x80` counts as a measurement | `test_status_tagged_data_reply_is_accepted`, `test_bare_success_status_for_a_read_is_not_mistaken_for_data`, `test_error_status_for_a_read_still_raises_command_error` |
| R-2 | Major | The contract promised a retry on timeout; the driver retried framing errors only. Measured: one attempt, no retry. A timeout is the most likely transient fault on a TTL adapter | `BK8500TimeoutError` is now retried alongside `BK8500ProtocolError`. The transport already flushes the input buffer before each write, so a late frame cannot be read as the next reply | `test_timeouts_are_retried` |
| R-3 | Major | `configure_list` validated each step as it wrote it. A bad step 3 left step count 3 with two steps written; step 3 played back as zero — silently wrong test data | Every step and the list name are validated before the first frame is sent. A rejected profile leaves the existing list untouched | `test_invalid_list_step_leaves_the_instrument_untouched`, `test_invalid_list_name_is_caught_before_any_step_is_written` |
| R-4 | Major | `package-data` pointed outside the package (`../../ai/*.yaml`), which setuptools ignores. The wheel contained no contract, so an installed driver had no RFDS-017 deliverable | `ai/` moved inside the package; `contract_path()` and `lock_path()` locate it in an installed environment. Verified present in the built wheel | `test_installed_contract_is_locatable` |
| R-5 | Minor | Replies were not address-checked; a frame from address 7 was accepted by a driver addressed to 0 | The address is validated as part of frame well-formedness, and a mismatch is retried like any framing fault | `test_reply_from_another_address_is_rejected` |
| R-6 | Minor | Every capability declared `stabilization_delay_s`, but the driver applied only a flat global delay defaulting to zero. The contract described behaviour the code did not have | Delays are applied from `STABILIZATION_DELAYS_S`, keyed to the operations that declare them, and can be disabled with `apply_stabilization_delays=False`. The contract now states which side owns the delay | `test_stabilization_delays_are_applied`, `test_stabilization_delays_can_be_disabled` |
| R-7 | Minor | `Close Load Connection` silently re-pointed "current" at an arbitrary surviving alias | The current connection is cleared instead, with a log line naming what remains open. A keyword issued without switching now fails loudly | `test_closing_the_current_connection_does_not_adopt_another` |
| R-8 | Minor | `generate_lock.py` would write a lock pinning zero keywords if Robot Framework were missing, silently disabling conformance rule CR-6 | The generator exits with an error when the keyword surface is empty | — (generator guard) |
| R-9 | Minor | `_validate` accepted `True` as 1.0 | Booleans are rejected with a message naming the type | `test_booleans_are_not_accepted_as_setpoints` |
| R-10 | Cosmetic | Confusing operator precedence in the simulator's operating-point guard | Split into two explicit conditions | — |
| R-11 | Open | Firmware version decoding assumes hexadecimal; the manual does not say whether it is hex or BCD | Undecoded bytes returned as `firmware_raw` for comparison against the front panel. Recorded as limitation LIM-12 | `test_product_info_exposes_raw_firmware_bytes` |

## Review outcome

- Critical issues: 1 found, 1 resolved.
- Major issues: 3 found, 3 resolved.
- Minor and cosmetic: 6 found, 6 resolved.
- Open: R-11 (needs hardware), F-1 (needs hardware).

## What the test results do and do not prove

63 pytest tests and 15 Robot tests pass, at 86 % statement coverage. Coverage
overstates the assurance: the simulator is this author's reading of the manual,
so most tests prove the driver agrees with itself. The independent evidence is
narrow — the checksum example (`0xCB`) and the 16.23 V, 3.12 A and 213.45 W
encodings taken from the manual's worked examples.

R-1 in particular cannot be closed by simulation. The driver now survives both
reply framings, but which one the firmware actually uses is unknown until an
instrument answers. This is the strongest argument for treating F-1 as
blocking.

## Gate 5 status

Deliverables complete: code review (this document), architecture review, Robot
API review, documentation review, bug fixes, changelog, release notes, ZIP
package.

**Gate 5 is not approved.** Acceptance requires no critical issues and major
issues resolved or documented; that is satisfied for the code, but the
regression and performance reviews cannot be completed without hardware
(F-1, R-11). The package is releasable as a pre-hardware engineering drop and
should not be recorded as a verified Phase 1 completion.


## Release 26.15 closure note

The original pre-hardware decision above is preserved as historical review
evidence. The physical v26.14 run later passed 56/56 tests on model 8500
firmware 1.84, closing the keyword-callability hardware finding. Release 26.15
preserves that report under `evidence/`. Raw RFDS-019 protocol traces and
multi-baud performance remain separate follow-up work.
