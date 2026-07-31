# Release v26.11 all-keyword conformance review

## Scope

Review of the new physical-device suite against the 55-keyword
`BK8500Library` surface and RFDS safety expectations.

## Findings

1. **Coverage completeness — PASS**  
   Static package validation compares the suite text with the live decorated
   keyword surface. Every exported keyword is referenced. A separate executable
   simulator test calls every keyword and fails on any missing coverage.

2. **Independent failure reporting — PASS**  
   Each public keyword has its own Robot test case. One command failure therefore
   does not prevent later test cases from being attempted, except when the common
   hardware connection or basic remote-control setup itself is unavailable.

3. **Response verification — PASS WITH PROTOCOL LIMITATION**  
   Setters with getters are verified by readback. Commands without a defined
   getter are verified by a successful status response and, where possible, by
   measurement state bits. The binary protocol provides no further response for
   commands such as software trigger or local-key setting beyond command status
   and state registers.

4. **Electrical safety — PASS**  
   Test setup and teardown force input OFF and FIXED mode. Input enable requires
   explicit opt-in and uses a low current setpoint. The unchecked function API is
   exercised with FIXED, never SHORT.

5. **Persistent side effects — PASS WITH OPERATOR ACTION**  
   List-file and settings-register tests are skipped unless explicitly enabled.
   The selected slots are configurable and documented as overwritten.

6. **Version clarity — PASS**  
   Python version `26.11.0` directly corresponds to ZIP release `v26.11`.
   Lifecycle phase/gate data remains separate.

## Residual risks

- Real-device results depend on the connected model, firmware behavior, adapter,
  DTR/RTS handling, source wiring and instrument storage contents.
- The suite changes volatile settings and, with persistent writes enabled,
  overwrites the selected storage slots.
- SHORT mode is intentionally not physically selected.

## Decision

Approved for release as a hardware-conformance-capable package. Hardware-verified
status requires attaching the resulting Robot reports from a real device run.
