# Migration to API 3.0

v26.07 removes the API 2 compatibility layer. Update tests before replacing an
older extracted driver folder.

| Removed keyword | Canonical replacement |
|---|---|
| Connect Climate Chamber | Connect |
| Disconnect Climate Chamber | Disconnect |
| Reconnect Climate Chamber | Reconnect |
| Get Climate Chamber Identification / Model / Serial Number / Manufacturing Year | Get Identity |
| Get Climate Chamber Library Version | Get Driver Information |
| Get Climate Chamber Connection Statistics / Health | Get Diagnostics |
| Get Climate Chamber Status | Get Chamber Status |
| Get Climate Chamber Temperature | Measure Temperature |
| Get Climate Chamber Setpoint | Get Temperature Setpoint |
| Set Climate Chamber Temperature | Set Temperature |
| Set/Get Climate Chamber Temperature Limits | Set/Get Temperature Limits |
| Start/Stop Climate Chamber | Start/Stop Chamber |
| Stop And Disconnect Climate Chamber | Safe Shutdown, then Disconnect |
| Set/Get Climate Chamber Heating Gradient | Set/Get Heating Gradient |
| Set/Get Climate Chamber Cooling Gradient | Set/Get Cooling Gradient |
| Set/Get Climate Chamber Dryer | Set/Get Dryer |
| Set/Get Climate Chamber Compressed Air | Set/Get Compressed Air |
| Wait Until Climate Chamber Is Stable | Wait For Temperature Stability |
| Wait For Climate Chamber Dwell | Wait For Dwell |
| Climate Chamber Temperature Should Be | Temperature Should Be |
| Climate Chamber Temperature Should Be Within | Temperature Should Be Within |
| Climate Chamber Setpoint Should Be | Temperature Setpoint Should Be |
| Climate Chamber Should Be Connected | Connection Should Be Available |
| Climate Chamber Should Be Running/Stopped | Chamber Should Be Running/Stopped |

## Connection argument migration

Do not pass the former positional sequence `ip, minimum, maximum` to `Connect`.
Use named canonical arguments:

```robotframework
Connect
...    resource=tcp://192.168.0.50:2049
...    alias=default
...    timeout_s=5 s
...    temperature_min_c=-40
...    temperature_max_c=180
```

Python imports must change from `votsch_climate_chamber...` to
`rf_votsch_climate_chamber...`.
