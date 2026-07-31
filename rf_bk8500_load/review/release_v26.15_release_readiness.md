# Release readiness — rf_bk8500_load_v26.15

## Verdict

**APPROVED for release as a documentation/evidence maintenance revision.**

## Release identity

- ZIP: `rf_bk8500_load_v26.15.zip`
- Distribution: `bk8500-load==26.15.0`
- Internal root: `rf_bk8500_load/`
- Public keywords: 55
- Functional core: unchanged from v26.14

## Evidence

- 56/56 physical Robot tests passed on the verified v26.14 core.
- Original reports and generated indexes are included.
- Core source hashes match v26.14.
- AI contract revision 11 records the evidence and scope.
- Documentation and package metadata are synchronised.
- 103 pytest checks passed; wheel build and clean metadata installation passed.

## Open non-blocking items

- RFDS-019 Levels 2–4 raw trace/vector/error-recovery bundle.
- Multi-baud transaction-time characterisation.
- Independent physical measurement-accuracy verification, which is outside
  this keyword callability suite.
