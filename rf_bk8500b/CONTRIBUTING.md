# Contributing

Every change must update tests and the requirement traceability matrix. Changes to public API, protocol assumptions, safety semantics, timeout/retry policy, dependencies, or repository layout require an ADR under `docs/adr/`.

Do not add undocumented protocol guesses. Mark an affected feature `BLOCKED` or `EXPERIMENTAL` and add a validation plan instead.

Run:

```bash
python -m pytest
python -m compileall -q bk8500b
```
