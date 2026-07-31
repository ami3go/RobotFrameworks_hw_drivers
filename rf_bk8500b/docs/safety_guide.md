# Safety guide

## Prohibited implicit actions

Construction, connection, identification, protocol probing, synchronization, reconnection, diagnostics, health checks, and cleanup must not enable input, enable short, trigger, reset, recall state, or clear protection.

## High-risk operations

- Input ON can require `SafetyToken.issue("enable_input")` when configured.
- Short mode requires `SafetyPolicy.allow_short=True` and `SafetyToken.issue("enable_short")`.
- Protection clear requires `SafetyToken.issue("clear_protection")`.
- Unknown models are blocked from hazards by default.
- Reconfiguration while input is ON is blocked by default.

## Indeterminate outcomes

Never automatically repeat an input-enable, trigger, reset, recall, protection-clear, OCP-start, timing-start, or raw write after timeout. Query the state, isolate the DUT if necessary, and require operator intervention when state cannot be proven.

## External controls

Use fuses, contactors, emergency stops, DUT current limiting, thermal monitoring, and a bench design that reaches a safe condition independently of Python or serial communication.
