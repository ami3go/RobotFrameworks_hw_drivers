---
layout: default
title: BK8500Library
---

# BK8500Library

Robot Framework driver for B&K Precision 8500-series DC electronic loads.

**Package release:** v26.16  
**Driver version:** 26.16.0  
**Lifecycle:** Phase 1, Gate 5 maintenance revision 11

## Automatic baud detection

Use `baudrate=AUTO` or set `auto_detect_baudrate=${TRUE}` on
`Open Load Connection`. The driver tries the requested rate first and then the
remaining configured rates. Probing sends only product-information query
`0x6A`, rejects local echo and invalid identities, and accepts a baud only after
two matching identities by default.

```robotframework
Open Load Connection    port=COM12    baudrate=AUTO
${info}=    Get Load Connection Info
Log    Selected baud=${info}[baudrate]
```

## Verified hardware status

The preserved v26.14 physical run passed **56/56** tests on model 8500, serial
`1687710135`, firmware `1.84`, through COM12 at 9600 baud. Release v26.16 keeps
that response path and adds automated baud selection. A physical fallback run
at a changed instrument baud remains the feature-specific closure test.

## Documentation

- [User guide](user_guide.md)
- [Architecture](architecture.md)
- [Keyword reference](BK8500Library.html)
- [AI integration](ai_integration.md)
- [PyCharm and Robot Framework setup](pycharm_robot_framework_setup.md)
- [Hardware connection](hardware_connection.md)
- [Troubleshooting](troubleshooting.md)
- [Examples](examples.md)
- [Hardware all-keyword test](../hardware_tests/README.md)
- [Release notes](release_notes.md)
