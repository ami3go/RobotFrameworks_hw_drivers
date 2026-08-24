"""Static capability registry for the implemented D0 slice."""

CAPABILITY_IDS = tuple(sorted({
    "connection",
    "identity",
    "multi_connection",
    "error_queue",
    "simulation",
    "module_discovery",
    "scpi_version",
}))

CAPABILITIES_NOT_APPLICABLE = {
    "channel_selection": "Deferred until channel/module capability implementation phase.",
    "output_control": "No generic output-control group is exposed in the current D0 slice.",
    "relay_control": "Deferred to switching/routing implementation phase.",
    "device_reset": "Deferred because *RST is state-changing and requires completed safety review.",
    "file_transfer": "34972A-only file functionality is deferred to the model-specific phase.",
    "safe_shutdown": "No persistent output-changing public keywords are exposed in this D0 slice.",
    "raw_io": "Raw I/O is intentionally disabled until safety and state invalidation rules are complete.",
    "dc_voltage_source": "Not a mainframe-wide capability; 34907A DAC support is deferred.",
    "dc_current_source": "Not supported as a generic source capability by this driver plan.",
    "electronic_load": "Not applicable to 34970A/34972A.",
    "temperature_control": "The device measures temperature; it does not control chamber temperature.",
    "resistance_simulation": "Not applicable to 34970A/34972A.",
    "waveform_generation": "Not applicable to 34970A/34972A.",
    "digital_io": "34907A digital I/O is deferred to its dedicated implementation phase.",
}
