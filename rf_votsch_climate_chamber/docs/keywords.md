# Canonical Robot Framework Keywords — v26.09

This API contains **58 canonical keywords**. API 2 compatibility aliases
were removed in v26.07; see [migration.md](migration.md).

## Cancel Current Operation

- Python method: `cancel_current_operation`
- Signature: `(self, alias: 'str | None' = None) -> 'None'`
- Return type: `None`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:operation, rfds:high_risk`

See generated Libdoc.

## Chamber Should Be Running

- Python method: `chamber_should_be_running`
- Signature: `(self, alias: 'str | None' = None) -> 'None'`
- Return type: `None`
- Device-facing: `yes`
- Protocol vector: `VCC-CHAMBER_SHOULD_BE_RUNNING-001`
- Tags: `rfds:assertion, rfds:none_risk`

See generated Libdoc.

## Chamber Should Be Stopped

- Python method: `chamber_should_be_stopped`
- Signature: `(self, alias: 'str | None' = None) -> 'None'`
- Return type: `None`
- Device-facing: `yes`
- Protocol vector: `VCC-CHAMBER_SHOULD_BE_STOPPED-001`
- Tags: `rfds:assertion, rfds:none_risk`

See generated Libdoc.

## Check Communication

- Python method: `check_communication`
- Signature: `(self, alias: 'str | None' = None) -> 'bool'`
- Return type: `bool`
- Device-facing: `yes`
- Protocol vector: `VCC-CHECK_COMMUNICATION-001`
- Tags: `rfds:connection, rfds:none_risk`

Perform a bounded non-destructive chamber-status query and return ``True``.

## Connect

- Python method: `connect`
- Signature: `(self, resource: 'str | None' = None, alias: 'str' = 'default', timeout_s: 'float | str | None' = None, **options: 'Any') -> 'dict[str, Any]'`
- Return type: `dict[str, Any]`
- Device-facing: `yes`
- Protocol vector: `VCC-CONNECT-001`
- Tags: `rfds:connection, rfds:low_risk`

Connect a chamber or simulator and return a ``connection_state`` dictionary.

``resource`` accepts ``tcp://host:port``, ``host``, ``host:port``, or
``SIM::<profile>``.  Connection is idempotent for the same alias and
normalized resource.  Functional chamber state is not changed.

## Connection Should Be Available

- Python method: `connection_should_be_available`
- Signature: `(self, alias: 'str | None' = None) -> 'None'`
- Return type: `None`
- Device-facing: `yes`
- Protocol vector: `VCC-CONNECTION_SHOULD_BE_AVAILABLE-001`
- Tags: `rfds:assertion, rfds:none_risk`

See generated Libdoc.

## Delete Driver Configuration Profile

- Python method: `delete_driver_configuration_profile`
- Signature: `(self, profile_name: 'str', confirm: 'bool | str' = False) -> 'dict[str, Any]'`
- Return type: `dict[str, Any]`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:configuration, rfds:destructive`

See generated Libdoc.

## Disconnect

- Python method: `disconnect`
- Signature: `(self, alias: 'str | None' = None) -> 'None'`
- Return type: `None`
- Device-facing: `yes`
- Protocol vector: `VCC-DISCONNECT-001`
- Tags: `rfds:connection, rfds:high_risk`

Apply the configured safe state, close the session, and release resources.

The operation is idempotent.  It is bounded by a 20 s cleanup budget.

## Disconnect All

- Python method: `disconnect_all`
- Signature: `(self) -> 'None'`
- Return type: `None`
- Device-facing: `yes`
- Protocol vector: `VCC-DISCONNECT_ALL-001`
- Tags: `rfds:connection, rfds:high_risk`

See generated Libdoc.

## Export Diagnostic Bundle

- Python method: `export_diagnostic_bundle`
- Signature: `(self, destination: 'str | None' = None) -> 'str | None'`
- Return type: `str | None`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:diagnostics, rfds:low_risk`

Zip this session's RFDS-008 live evidence run for troubleshooting.

Different from ``Export Diagnostics``: that keyword writes one
point-in-time state snapshot; this zips the whole append-only
evidence run recorded so far (every keyword call, every SimServ
protocol frame, every error, correlated and integrity-hashed) —
see ``evidence.py`` and the "Evidence and Diagnostics" section of
``docs/TROUBLESHOOTING.md``. Safe to call whether or not any alias is
currently connected; does not finalize the run (suite end does).
Returns the archive path, or ``None`` if evidence is disabled.

## Export Diagnostics

- Python method: `export_diagnostics`
- Signature: `(self, destination: 'str') -> 'dict[str, Any]'`
- Return type: `dict[str, Any]`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:diagnostics, rfds:low_risk`

See generated Libdoc.

## Export Driver Configuration

- Python method: `export_driver_configuration`
- Signature: `(self, destination: 'str | None' = None, scope: 'str' = 'EFFECTIVE', profile_name: 'str | None' = None, overwrite: 'bool | str' = False, alias: 'str | None' = None) -> 'dict[str, Any]'`
- Return type: `dict[str, Any]`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:configuration, rfds:low_risk`

See generated Libdoc.

## Get Active Connection

- Python method: `get_active_connection`
- Signature: `(self) -> 'str | None'`
- Return type: `str | None`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:connection, rfds:none_risk`

See generated Libdoc.

## Get Capability Model

- Python method: `get_capability_model`
- Signature: `(self) -> 'list[dict[str, Any]]'`
- Return type: `list[dict[str, Any]]`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:metadata, rfds:none_risk`

See generated Libdoc.

## Get Chamber Running State

- Python method: `get_chamber_running_state`
- Signature: `(self, alias: 'str | None' = None) -> 'bool'`
- Return type: `bool`
- Device-facing: `yes`
- Protocol vector: `VCC-GET_CHAMBER_RUNNING_STATE-001`
- Tags: `rfds:operation, rfds:none_risk`

See generated Libdoc.

## Get Chamber Status

- Python method: `get_chamber_status`
- Signature: `(self, alias: 'str | None' = None) -> 'str'`
- Return type: `str`
- Device-facing: `yes`
- Protocol vector: `VCC-GET_CHAMBER_STATUS-001`
- Tags: `rfds:diagnostics, rfds:none_risk`

See generated Libdoc.

## Get Communication Timeout

- Python method: `get_communication_timeout`
- Signature: `(self, alias: 'str | None' = None) -> 'float'`
- Return type: `float`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:connection, rfds:none_risk`

Return the selected session timeout or the unconnected driver default.

## Get Compressed Air

- Python method: `get_compressed_air`
- Signature: `(self, alias: 'str | None' = None) -> 'bool'`
- Return type: `bool`
- Device-facing: `yes`
- Protocol vector: `VCC-GET_COMPRESSED_AIR-001`
- Tags: `rfds:digital_io, rfds:none_risk`

Read compressed air; fail if no physical channel mapping was qualified.

## Get Connection State

- Python method: `get_connection_state`
- Signature: `(self, alias: 'str | None' = None, refresh: 'bool | str' = False) -> 'dict[str, Any]'`
- Return type: `dict[str, Any]`
- Device-facing: `yes`
- Protocol vector: `VCC-GET_CONNECTION_STATE-001`
- Tags: `rfds:connection, rfds:none_risk`

Return stable connection-state fields; optionally perform a safe live probe.

## Get Cooling Gradient

- Python method: `get_cooling_gradient`
- Signature: `(self, alias: 'str | None' = None) -> 'float'`
- Return type: `float`
- Device-facing: `yes`
- Protocol vector: `VCC-GET_COOLING_GRADIENT-001`
- Tags: `rfds:temperature_control, rfds:none_risk`

See generated Libdoc.

## Get Diagnostics

- Python method: `get_diagnostics`
- Signature: `(self) -> 'dict[str, Any]'`
- Return type: `dict[str, Any]`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:diagnostics, rfds:none_risk`

See generated Libdoc.

## Get Driver Capabilities

- Python method: `get_driver_capabilities`
- Signature: `(self) -> 'list[str]'`
- Return type: `list[str]`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:metadata, rfds:none_risk`

Return the sorted RFDS-002 capability identifiers.

## Get Driver Configuration

- Python method: `get_driver_configuration`
- Signature: `(self, scope: 'str' = 'EFFECTIVE', alias: 'str | None' = None, redact_sensitive: 'bool | str' = True, include_sources: 'bool | str' = False) -> 'dict[str, Any]'`
- Return type: `dict[str, Any]`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:configuration, rfds:none_risk`

See generated Libdoc.

## Get Driver Configuration Schema

- Python method: `get_driver_configuration_schema`
- Signature: `(self) -> 'dict[str, Any]'`
- Return type: `dict[str, Any]`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:configuration, rfds:none_risk`

See generated Libdoc.

## Get Driver Default Configuration

- Python method: `get_driver_default_configuration`
- Signature: `(self, redact_sensitive: 'bool | str' = True) -> 'dict[str, Any]'`
- Return type: `dict[str, Any]`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:configuration, rfds:none_risk`

See generated Libdoc.

## Get Driver Information

- Python method: `get_driver_information`
- Signature: `(self) -> 'dict[str, Any]'`
- Return type: `dict[str, Any]`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:metadata, rfds:none_risk`

Return static driver metadata without device I/O.

## Get Dryer

- Python method: `get_dryer`
- Signature: `(self, alias: 'str | None' = None) -> 'bool'`
- Return type: `bool`
- Device-facing: `yes`
- Protocol vector: `VCC-GET_DRYER-001`
- Tags: `rfds:digital_io, rfds:none_risk`

Read the configured dryer output; fail if no mapping was qualified.

## Get Heating Gradient

- Python method: `get_heating_gradient`
- Signature: `(self, alias: 'str | None' = None) -> 'float'`
- Return type: `float`
- Device-facing: `yes`
- Protocol vector: `VCC-GET_HEATING_GRADIENT-001`
- Tags: `rfds:temperature_control, rfds:none_risk`

See generated Libdoc.

## Get Identity

- Python method: `get_identity`
- Signature: `(self, alias: 'str | None' = None, refresh: 'bool | str' = False) -> 'str'`
- Return type: `str`
- Device-facing: `yes`
- Protocol vector: `VCC-GET_IDENTITY-001`
- Tags: `rfds:identity, rfds:none_risk`

Return cached connection identity by default; ``refresh=True`` queries the chamber.

## Get Temperature Limits

- Python method: `get_temperature_limits`
- Signature: `(self, alias: 'str | None' = None) -> 'dict[str, Any]'`
- Return type: `dict[str, Any]`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:temperature_control, rfds:none_risk`

See generated Libdoc.

## Get Temperature Setpoint

- Python method: `get_temperature_setpoint`
- Signature: `(self, alias: 'str | None' = None) -> 'float'`
- Return type: `float`
- Device-facing: `yes`
- Protocol vector: `VCC-GET_TEMPERATURE_SETPOINT-001`
- Tags: `rfds:temperature_control, rfds:none_risk`

See generated Libdoc.

## Import Driver Configuration

- Python method: `import_driver_configuration`
- Signature: `(self, source: 'Any', mode: 'str' = 'REPLACE', apply: 'bool | str' = False, persist: 'bool | str' = False, profile_name: 'str | None' = None, strict: 'bool | str' = True, reconnect: 'bool | str' = False, allow_device_persistent_changes: 'bool | str' = False, confirm_high_risk: 'bool | str' = False, alias: 'str | None' = None) -> 'dict[str, Any]'`
- Return type: `dict[str, Any]`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:configuration, rfds:medium_risk`

See generated Libdoc.

## Is Connected

- Python method: `is_connected`
- Signature: `(self, alias: 'str | None' = None) -> 'bool'`
- Return type: `bool`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:connection, rfds:none_risk`

Return cached transport state without device I/O.

## List Connections

- Python method: `list_connections`
- Signature: `(self) -> 'list[dict[str, Any]]'`
- Return type: `list[dict[str, Any]]`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:connection, rfds:none_risk`

See generated Libdoc.

## List Driver Configuration Profiles

- Python method: `list_driver_configuration_profiles`
- Signature: `(self) -> 'list[dict[str, Any]]'`
- Return type: `list[dict[str, Any]]`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:configuration, rfds:none_risk`

See generated Libdoc.

## Load Driver Configuration

- Python method: `load_driver_configuration`
- Signature: `(self, profile_name: 'str', apply: 'bool | str' = False, reconnect: 'bool | str' = False, alias: 'str | None' = None) -> 'dict[str, Any]'`
- Return type: `dict[str, Any]`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:configuration, rfds:low_risk`

See generated Libdoc.

## Measure Temperature

- Python method: `measure_temperature`
- Signature: `(self, alias: 'str | None' = None) -> 'float'`
- Return type: `float`
- Device-facing: `yes`
- Protocol vector: `VCC-MEASURE_TEMPERATURE-001`
- Tags: `rfds:temperature_measurement, rfds:none_risk`

Trigger a live chamber temperature query and return degrees Celsius.

## Reconnect

- Python method: `reconnect`
- Signature: `(self, alias: 'str | None' = None) -> 'dict[str, Any]'`
- Return type: `dict[str, Any]`
- Device-facing: `yes`
- Protocol vector: `VCC-RECONNECT-001`
- Tags: `rfds:connection, rfds:low_risk`

See generated Libdoc.

## Reset Driver Configuration

- Python method: `reset_driver_configuration`
- Signature: `(self, path: 'str | None' = None, scope: 'str' = 'INSTANCE_OVERRIDE', apply: 'bool | str' = False, persist: 'bool | str' = False, confirm: 'bool | str' = False, alias: 'str | None' = None) -> 'dict[str, Any]'`
- Return type: `dict[str, Any]`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:configuration, rfds:medium_risk`

See generated Libdoc.

## Safe Shutdown

- Python method: `safe_shutdown`
- Signature: `(self, alias: 'str | None' = None, timeout_s: 'float | str | None' = None) -> 'dict[str, Any]'`
- Return type: `dict[str, Any]`
- Device-facing: `yes`
- Protocol vector: `VCC-SAFE_SHUTDOWN-001`
- Tags: `rfds:safe_shutdown, rfds:high_risk`

Stop the chamber and disable only configured auxiliary outputs.

Unqualified dryer and compressed-air mappings are recorded as ``SKIP``
rather than transmitted to an unknown digital-output channel.

## Save Driver Configuration

- Python method: `save_driver_configuration`
- Signature: `(self, profile_name: 'str', scope: 'str' = 'EFFECTIVE', overwrite: 'bool | str' = False, set_active: 'bool | str' = False, alias: 'str | None' = None) -> 'dict[str, Any]'`
- Return type: `dict[str, Any]`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:configuration, rfds:low_risk`

See generated Libdoc.

## Select Connection

- Python method: `select_connection`
- Signature: `(self, alias: 'str') -> 'dict[str, Any]'`
- Return type: `dict[str, Any]`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:connection, rfds:low_risk`

See generated Libdoc.

## Set Communication Timeout

- Python method: `set_communication_timeout`
- Signature: `(self, timeout_s: 'float | str', alias: 'str | None' = None) -> 'float'`
- Return type: `float`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:connection, rfds:low_risk`

Apply a finite positive communication timeout and return seconds.

## Set Compressed Air

- Python method: `set_compressed_air`
- Signature: `(self, enabled: 'bool | str', alias: 'str | None' = None) -> 'None'`
- Return type: `None`
- Device-facing: `yes`
- Protocol vector: `VCC-SET_COMPRESSED_AIR-001`
- Tags: `rfds:digital_io, rfds:medium_risk`

Set compressed air using the explicitly configured physical channel.

## Set Cooling Gradient

- Python method: `set_cooling_gradient`
- Signature: `(self, value_c_per_min: 'float', alias: 'str | None' = None) -> 'None'`
- Return type: `None`
- Device-facing: `yes`
- Protocol vector: `VCC-SET_COOLING_GRADIENT-001`
- Tags: `rfds:temperature_control, rfds:medium_risk`

See generated Libdoc.

## Set Dryer

- Python method: `set_dryer`
- Signature: `(self, enabled: 'bool | str', alias: 'str | None' = None) -> 'None'`
- Return type: `None`
- Device-facing: `yes`
- Protocol vector: `VCC-SET_DRYER-001`
- Tags: `rfds:digital_io, rfds:medium_risk`

Set the dryer output using the explicitly configured physical channel.

Real hardware defaults to unsupported until ``dryer_output_channel`` is
supplied through configuration or ``Connect`` options.

## Set Heating Gradient

- Python method: `set_heating_gradient`
- Signature: `(self, value_c_per_min: 'float', alias: 'str | None' = None) -> 'None'`
- Return type: `None`
- Device-facing: `yes`
- Protocol vector: `VCC-SET_HEATING_GRADIENT-001`
- Tags: `rfds:temperature_control, rfds:medium_risk`

See generated Libdoc.

## Set Temperature

- Python method: `set_temperature`
- Signature: `(self, value_c: 'float', alias: 'str | None' = None) -> 'None'`
- Return type: `None`
- Device-facing: `yes`
- Protocol vector: `VCC-SET_TEMPERATURE-001`
- Tags: `rfds:temperature_control, rfds:high_risk`

See generated Libdoc.

## Set Temperature And Wait

- Python method: `set_temperature_and_wait`
- Signature: `(self, value_c: 'float', dwell_s: 'float | str' = 0.0, tolerance_c: 'float' = 0.8, poll_interval_s: 'float | str' = 10.0, settle_timeout_s: 'float | str' = 14400.0, stable_samples: 'int' = 3, start_chamber: 'bool | str' = True, alias: 'str | None' = None) -> 'float'`
- Return type: `float`
- Device-facing: `yes`
- Protocol vector: `VCC-SET_TEMPERATURE_AND_WAIT-001`
- Tags: `rfds:temperature_control, rfds:high_risk, rfds:long_running`

See generated Libdoc.

## Set Temperature Limits

- Python method: `set_temperature_limits`
- Signature: `(self, minimum_c: 'float', maximum_c: 'float', alias: 'str | None' = None) -> 'dict[str, Any]'`
- Return type: `dict[str, Any]`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:temperature_control, rfds:low_risk`

See generated Libdoc.

## Start Chamber

- Python method: `start_chamber`
- Signature: `(self, alias: 'str | None' = None) -> 'None'`
- Return type: `None`
- Device-facing: `yes`
- Protocol vector: `VCC-START_CHAMBER-001`
- Tags: `rfds:operation, rfds:high_risk`

See generated Libdoc.

## Stop Chamber

- Python method: `stop_chamber`
- Signature: `(self, alias: 'str | None' = None) -> 'None'`
- Return type: `None`
- Device-facing: `yes`
- Protocol vector: `VCC-STOP_CHAMBER-001`
- Tags: `rfds:operation, rfds:high_risk`

See generated Libdoc.

## Temperature Setpoint Should Be

- Python method: `temperature_setpoint_should_be`
- Signature: `(self, expected_c: 'float', tolerance_c: 'float' = 0.05, alias: 'str | None' = None) -> 'None'`
- Return type: `None`
- Device-facing: `yes`
- Protocol vector: `VCC-TEMPERATURE_SETPOINT_SHOULD_BE-001`
- Tags: `rfds:assertion, rfds:none_risk`

See generated Libdoc.

## Temperature Should Be

- Python method: `temperature_should_be`
- Signature: `(self, expected_c: 'float', tolerance_c: 'float' = 0.1, alias: 'str | None' = None) -> 'None'`
- Return type: `None`
- Device-facing: `yes`
- Protocol vector: `VCC-TEMPERATURE_SHOULD_BE-001`
- Tags: `rfds:assertion, rfds:none_risk`

See generated Libdoc.

## Temperature Should Be Within

- Python method: `temperature_should_be_within`
- Signature: `(self, minimum_c: 'float', maximum_c: 'float', alias: 'str | None' = None) -> 'None'`
- Return type: `None`
- Device-facing: `yes`
- Protocol vector: `VCC-TEMPERATURE_SHOULD_BE_WITHIN-001`
- Tags: `rfds:assertion, rfds:none_risk`

See generated Libdoc.

## Validate Driver Configuration

- Python method: `validate_driver_configuration`
- Signature: `(self, configuration: 'Any', mode: 'str' = 'REPLACE', strict: 'bool | str' = True, alias: 'str | None' = None) -> 'dict[str, Any]'`
- Return type: `dict[str, Any]`
- Device-facing: `no`
- Protocol vector: `N/A`
- Tags: `rfds:configuration, rfds:none_risk`

See generated Libdoc.

## Wait For Dwell

- Python method: `wait_for_dwell`
- Signature: `(self, duration_s: 'float | str', poll_interval_s: 'float | str' = 60.0, alias: 'str | None' = None) -> 'float'`
- Return type: `float`
- Device-facing: `yes`
- Protocol vector: `VCC-WAIT_FOR_DWELL-001`
- Tags: `rfds:temperature_measurement, rfds:medium_risk, rfds:long_running`

See generated Libdoc.

## Wait For Temperature Stability

- Python method: `wait_for_temperature_stability`
- Signature: `(self, target_c: 'float | None' = None, tolerance_c: 'float' = 0.8, stable_samples: 'int' = 3, poll_interval_s: 'float | str' = 10.0, settle_timeout_s: 'float | str' = 14400.0, alias: 'str | None' = None) -> 'float'`
- Return type: `float`
- Device-facing: `yes`
- Protocol vector: `VCC-WAIT_FOR_TEMPERATURE_STABILITY-001`
- Tags: `rfds:temperature_measurement, rfds:high_risk, rfds:long_running`

See generated Libdoc.
