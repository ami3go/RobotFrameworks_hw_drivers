# Release checklist

## Gates G0–G6 software candidate

- [x] Root-level package and frozen API candidate
- [x] Requirement and command traceability documents
- [x] Finite transport/execution paths
- [x] SCPI and legacy codec tests
- [x] Fake-instrument integration and fault injection
- [x] Production package statement coverage at least 95%
- [x] Production package branch coverage at least 90%
- [x] Legacy codec branch coverage 100%
- [x] Safety documentation, examples, CLI, wheel/sdist metadata
- [x] Wheel installation, CLI, and installed-artifact test suite verified locally
- [x] Wheel rebuild from source distribution verified locally
- [ ] Hosted Windows 11 CI passed
- [ ] Hosted current Ubuntu LTS CI passed

## Gate G7 — hardware validation

- [ ] Original PDF cross-check
- [ ] SCPI terminators confirmed
- [ ] Per-model/firmware matrix complete
- [ ] Every stable command has capture/evidence
- [ ] Legacy response status/scaling ambiguities resolved
- [ ] Independent measurement comparison passed

## Gate G8 — endurance

- [ ] 168-hour soak passed
- [ ] 1,000 open/close cycles passed
- [ ] Resource-leak analysis passed
- [ ] Failure/recovery and wrong-device HIL tests passed
- [ ] No waived critical issue
- [ ] Explicit production approval recorded
