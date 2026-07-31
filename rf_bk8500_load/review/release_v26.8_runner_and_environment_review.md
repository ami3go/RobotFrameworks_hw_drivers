# Runner and environment review — release v26.8

## Findings

1. **Critical usability defect:** An existing `.venv` was accepted solely
   because `python.exe` existed. The runner did not verify Robot Framework,
   pyserial, or the installed driver.
2. **Major path defect:** Documentation allowed users to work from the examples
   area, but no launcher existed there.
3. **Consistency defect:** Windows batch runners did not expose hardware port
   selection consistently.

## Corrections reviewed

- Canonical PowerShell and shell runners call a shared environment verifier.
- Incomplete environments invoke the setup script and are verified again.
- BAT runners perform an equivalent import check and setup fallback.
- `examples/` wrappers delegate to canonical scripts, avoiding duplicated run
  logic.
- Simulator and port variables are forwarded explicitly.
- Setup failures terminate with a non-zero result instead of continuing into a
  misleading Robot import error.

## Safety assessment

The correction changes only launch/bootstrap behavior. Hardware mode still
requires explicit `-Simulated:$false`; the default remains simulated. No load
input safety interlock or keyword behavior changed.

## Decision

Approved for release v26.8, with physical hardware verification still open.
