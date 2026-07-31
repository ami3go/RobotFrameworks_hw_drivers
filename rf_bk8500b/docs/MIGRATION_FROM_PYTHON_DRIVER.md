# Migration from the Python Driver

| Python driver | Robot Framework keyword |
|---|---|
| `device.connect()` | `Connect To Electronic Load` |
| `device.close()` | `Disconnect Electronic Load` |
| `device.identify()` | `Identify Electronic Load` |
| `device.set_operating_mode(OperatingMode.CURRENT)` | `Set Electronic Load Mode    CC` |
| `device.set_current_setpoint(1.0)` | `Set Current Setpoint    1.0` |
| `device.configure_and_enable(...)` | `Configure And Enable Load` |
| `device.measure_voltage()` | `Measure Voltage` |
| `device.measure_all()` | `Get Measurement Snapshot` |
| `device.health_check()` | `Run Electronic Load Health Check` |
| `device.drain_error_queue()` | `Drain Electronic Load Error Queue` |
| `device.query_raw_scpi(...)` | `Query Raw SCPI` |

Driver dataclasses become dictionaries. Enum members become their string values. Measurement objects are simplified to floats in the direct measurement keywords, while full metadata remains available through `Get Measurement Snapshot`.
