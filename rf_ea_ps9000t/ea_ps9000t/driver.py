"""Typed core driver for the Elektro-Automatik EA-PS 9000 T DC laboratory power supply.

Owns SCPI command construction and response parsing. The Robot Framework
adapter (``rf_ea_ps9000t/library.py``) is a thin layer on top of this
module and must not duplicate any of this logic (task §5).
"""

from __future__ import annotations

import logging

from .enums import AlarmAction, OutputRestoreMode, PowerStageAfterRemote, RemoteControlOwner
from .exceptions import (
    EaPs9000TConnectionError,
    EaPs9000TDeviceError,
    EaPs9000TValidationError,
)
from .models import (
    AdjustmentLimits,
    AlarmCounters,
    InstrumentIdentity,
    MeasuredValues,
    NominalRatings,
    ProtectionThresholds,
)
from .simulator import SimEaPs9000TInstrument
from .transport import PyvisaTransport, SimulatedTransport, Transport

logger = logging.getLogger(__name__)

_RAW_SCPI_CONFIRMATION = "ENABLE RAW SCPI"


class EaPs9000T:
    """A connected session with one EA-PS 9000 T instrument."""

    def __init__(self, transport: Transport) -> None:
        self.transport = transport
        self._identity: InstrumentIdentity | None = None
        self._raw_scpi_enabled = False

    # ------------------------------------------------------------------
    # Construction / lifecycle
    # ------------------------------------------------------------------
    @classmethod
    def connect_visa(cls, resource: str, timeout_s: float = 5.0) -> EaPs9000T:
        transport = PyvisaTransport(resource, timeout_s=timeout_s)
        transport.open()
        driver = cls(transport)
        driver.acquire_remote_control()
        return driver

    @classmethod
    def connect_simulated(cls, simulator: SimEaPs9000TInstrument | None = None) -> EaPs9000T:
        transport = SimulatedTransport(simulator)
        transport.open()
        driver = cls(transport)
        driver.acquire_remote_control()
        return driver

    def close(self) -> None:
        try:
            self.release_remote_control()
        except Exception:  # noqa: BLE001, S110 - best-effort: the transport is closing
            # regardless, and a real device that's already gone can't be released anyway.
            pass
        self.transport.close()

    @property
    def connected(self) -> bool:
        return self.transport.is_open()

    @property
    def resource(self) -> str:
        return self.transport.resource

    @property
    def timeout_s(self) -> float:
        return self.transport.timeout_s

    @timeout_s.setter
    def timeout_s(self, value: float) -> None:
        self.transport.timeout_s = value

    # ------------------------------------------------------------------
    # Low-level I/O with exception translation
    # ------------------------------------------------------------------
    def _require_connected(self) -> None:
        if not self.transport.is_open():
            raise EaPs9000TConnectionError("not connected; call connect_visa/connect_simulated first")

    def _write(self, command: str) -> None:
        self._require_connected()
        self.transport.write(command)

    def _query(self, command: str) -> str:
        self._require_connected()
        return self.transport.query(command)

    def _check_events(self, context: str) -> None:
        """Raise if the instrument's SCPI error queue reports a problem after ``context``.

        Errors are never returned automatically on this instrument family
        (task §2) — they must be explicitly queried after every write that
        could plausibly fail, such as a set value that's outside the
        currently configured adjustment limits.
        """

        message = self._query("SYSTem:ERRor?").strip()
        if message.startswith("0,"):
            return
        raise EaPs9000TDeviceError(f"{context} failed: instrument reported an error: {message}")

    # ------------------------------------------------------------------
    # Remote control (task §6 items 1-2)
    # ------------------------------------------------------------------
    def acquire_remote_control(self) -> None:
        """Requests remote control and verifies the device actually granted it.

        The request can be refused (front panel in "Local" lock, already
        remote-controlled elsewhere, or the setup menu is open) and refusal
        surfaces as a SCPI error on the *next* command, not the lock request
        itself (task §2) — so this method explicitly re-queries
        ``SYSTem:LOCK:OWNer?`` after requesting the lock rather than trusting
        the write succeeded.
        """

        self._write("SYSTem:LOCK ON")
        owner = self.get_remote_control_owner()
        if owner != RemoteControlOwner.REMOTE:
            raise EaPs9000TConnectionError(
                f"remote control was refused; current owner is {owner.value!r} "
                "(check the front panel isn't in 'Local' lock condition, in the setup "
                "menu, or already remote-controlled via a different interface)"
            )

    def release_remote_control(self) -> None:
        self._write("SYSTem:LOCK OFF")

    def get_remote_control_owner(self) -> RemoteControlOwner:
        return RemoteControlOwner(self._query("SYSTem:LOCK:OWNer?").strip())

    # ------------------------------------------------------------------
    # Identity / communication (RFDS-002)
    # ------------------------------------------------------------------
    def identify(self, *, refresh: bool = True) -> InstrumentIdentity:
        if not refresh and self._identity is not None:
            return self._identity
        raw = self._query("*IDN?")
        parts = raw.strip().split(",", 4)  # up to 5 fields (task §6 item 6)
        identity = InstrumentIdentity(
            manufacturer=parts[0].strip() if len(parts) > 0 else "",
            model=parts[1].strip() if len(parts) > 1 else "",
            serial=parts[2].strip() if len(parts) > 2 else "",
            firmware=parts[3].strip() if len(parts) > 3 else "",
            user_text=parts[4].strip() if len(parts) > 4 else "",
            raw=raw.strip(),
        )
        self._identity = identity
        return identity

    def check_communication(self) -> bool:
        self._query("*IDN?")
        return True

    # ------------------------------------------------------------------
    # Set values (task §8)
    # ------------------------------------------------------------------
    def set_voltage(self, value: float) -> None:
        self._write(f"VOLTage {float(value)}")
        self._check_events("Set Voltage")

    def get_voltage(self) -> float:
        return float(self._query("VOLTage?"))

    def set_current(self, value: float) -> None:
        self._write(f"CURRent {float(value)}")
        self._check_events("Set Current")

    def get_current(self) -> float:
        return float(self._query("CURRent?"))

    def set_power(self, value: float) -> None:
        self._write(f"POWer {float(value)}")
        self._check_events("Set Power")

    def get_power(self) -> float:
        return float(self._query("POWer?"))

    # ------------------------------------------------------------------
    # Protection thresholds (task §8)
    # ------------------------------------------------------------------
    def set_overvoltage_protection(self, value: float) -> None:
        self._write(f"VOLTage:PROTection {float(value)}")
        self._check_events("Set Overvoltage Protection")

    def get_overvoltage_protection(self) -> float:
        return float(self._query("VOLTage:PROTection?"))

    def set_overcurrent_protection(self, value: float) -> None:
        self._write(f"CURRent:PROTection {float(value)}")
        self._check_events("Set Overcurrent Protection")

    def get_overcurrent_protection(self) -> float:
        return float(self._query("CURRent:PROTection?"))

    def set_overpower_protection(self, value: float) -> None:
        self._write(f"POWer:PROTection {float(value)}")
        self._check_events("Set Overpower Protection")

    def get_overpower_protection(self) -> float:
        return float(self._query("POWer:PROTection?"))

    def get_protection_thresholds(self) -> ProtectionThresholds:
        return ProtectionThresholds(
            overvoltage=self.get_overvoltage_protection(),
            overcurrent=self.get_overcurrent_protection(),
            overpower=self.get_overpower_protection(),
        )

    # ------------------------------------------------------------------
    # Output control (task §8)
    # ------------------------------------------------------------------
    def enable_output(self) -> None:
        self._write("OUTPut ON")
        self._check_events("Enable Output")

    def disable_output(self) -> None:
        self._write("OUTPut OFF")
        self._check_events("Disable Output")

    def is_output_enabled(self) -> bool:
        return self._query("OUTPut?").strip() in ("1", "ON")

    # ------------------------------------------------------------------
    # Measuring (task §8)
    # ------------------------------------------------------------------
    def get_measured_voltage(self) -> float:
        return float(self._query("MEASure:VOLTage?"))

    def get_measured_current(self) -> float:
        return float(self._query("MEASure:CURRent?"))

    def get_measured_power(self) -> float:
        return float(self._query("MEASure:POWer?"))

    def get_measured_values(self) -> MeasuredValues:
        raw = self._query("MEASure:ARRay?")
        parts = [p.strip() for p in raw.split(",")]
        values = [float(p.split()[0]) for p in parts]
        return MeasuredValues(voltage=values[0], current=values[1], power=values[2])

    # ------------------------------------------------------------------
    # General queries (task §8)
    # ------------------------------------------------------------------
    def get_nominal_ratings(self) -> NominalRatings:
        return NominalRatings(
            voltage=float(self._query("SYSTem:NOMinal:VOLTage?")),
            current=float(self._query("SYSTem:NOMinal:CURRent?")),
            power=float(self._query("SYSTem:NOMinal:POWer?")),
        )

    def get_device_class(self) -> str:
        return self._query("SYSTem:DEVice:CLASs?").strip()

    def get_alarm_counters(self) -> AlarmCounters:
        return AlarmCounters(
            overvoltage=int(self._query("SYSTem:ALARm:COUNt:OVOLtage?")),
            overtemperature=int(self._query("SYSTem:ALARm:COUNt:OTEMperature?")),
            overpower=int(self._query("SYSTem:ALARm:COUNt:OPOWer?")),
            overcurrent=int(self._query("SYSTem:ALARm:COUNt:OCURrent?")),
            power_fail=int(self._query("SYSTem:ALARm:COUNt:PFAil?")),
        )

    # ------------------------------------------------------------------
    # Adjustment limits (task §9)
    # ------------------------------------------------------------------
    def set_voltage_limit_low(self, value: float) -> None:
        self._write(f"VOLTage:LIMit:LOW {float(value)}")
        self._check_events("Set Voltage Limit Low")

    def set_voltage_limit_high(self, value: float) -> None:
        self._write(f"VOLTage:LIMit:HIGH {float(value)}")
        self._check_events("Set Voltage Limit High")

    def get_voltage_limits(self) -> tuple[float, float]:
        return (
            float(self._query("VOLTage:LIMit:LOW?")),
            float(self._query("VOLTage:LIMit:HIGH?")),
        )

    def set_current_limit_low(self, value: float) -> None:
        self._write(f"CURRent:LIMit:LOW {float(value)}")
        self._check_events("Set Current Limit Low")

    def set_current_limit_high(self, value: float) -> None:
        self._write(f"CURRent:LIMit:HIGH {float(value)}")
        self._check_events("Set Current Limit High")

    def get_current_limits(self) -> tuple[float, float]:
        return (
            float(self._query("CURRent:LIMit:LOW?")),
            float(self._query("CURRent:LIMit:HIGH?")),
        )

    def set_power_limit_high(self, value: float) -> None:
        """No corresponding "low" limit exists on this instrument family (task §9)."""

        self._write(f"POWer:LIMit:HIGH {float(value)}")
        self._check_events("Set Power Limit High")

    def get_power_limit_high(self) -> float:
        return float(self._query("POWer:LIMit:HIGH?"))

    def get_adjustment_limits(self) -> AdjustmentLimits:
        voltage_low, voltage_high = self.get_voltage_limits()
        current_low, current_high = self.get_current_limits()
        return AdjustmentLimits(
            voltage_low=voltage_low,
            voltage_high=voltage_high,
            current_low=current_low,
            current_high=current_high,
            power_high=self.get_power_limit_high(),
        )

    # ------------------------------------------------------------------
    # Device configuration (task §9, PST-applicable subset only)
    # ------------------------------------------------------------------
    def set_power_stage_after_remote(self, mode: PowerStageAfterRemote | str) -> None:
        mode = PowerStageAfterRemote(mode)
        self._write(f"POWer:STAGe:AFTer:REMote {mode.value}")
        self._check_events("Set Power Stage After Remote")

    def get_power_stage_after_remote(self) -> PowerStageAfterRemote:
        return PowerStageAfterRemote(self._query("POWer:STAGe:AFTer:REMote?").strip())

    def set_output_restore_mode(self, mode: OutputRestoreMode | str) -> None:
        mode = OutputRestoreMode(mode)
        self._write(f"SYSTem:CONFig:OUTPut:RESTore {mode.value}")
        self._check_events("Set Output Restore Mode")

    def get_output_restore_mode(self) -> OutputRestoreMode:
        return OutputRestoreMode(self._query("SYSTem:CONFig:OUTPut:RESTore?").strip())

    def set_user_text(self, text: str) -> None:
        if len(text) > 40:
            raise EaPs9000TValidationError("user text must be 40 characters or fewer")
        self._write(f'SYSTem:CONFig:USER:TEXT "{text}"')
        self._check_events("Set User Text")

    def get_user_text(self) -> str:
        return self._query("SYSTem:CONFig:USER:TEXT?").strip().strip('"')

    def set_communication_timeout(self, milliseconds: int) -> None:
        """Serial interfaces only (USB, RS232) — not meaningful over Ethernet (task §9);
        this driver does not client-side-gate on interface type since it has no
        reliable way to know which transport is active at the SCPI layer."""

        if not (5 <= int(milliseconds) <= 65535):
            raise EaPs9000TValidationError("communication timeout must be between 5 and 65535 ms")
        self._write(f"SYSTem:COMMunicate:TIMeout {int(milliseconds)}")
        self._check_events("Set Communication Timeout")

    def get_communication_timeout(self) -> int:
        return int(self._query("SYSTem:COMMunicate:TIMeout?"))

    def set_power_fail_alarm_action(self, action: AlarmAction | str) -> None:
        action = AlarmAction(action)
        self._write(f"SYSTem:ALARm:ACTion:PFail {action.value}")
        self._check_events("Set Power Fail Alarm Action")

    def get_power_fail_alarm_action(self) -> AlarmAction:
        return AlarmAction(self._query("SYSTem:ALARm:ACTion:PFail?").strip())

    def set_overtemperature_alarm_action(self, action: AlarmAction | str) -> None:
        action = AlarmAction(action)
        self._write(f"SYSTem:ALARm:ACTion:OTEMperature {action.value}")
        self._check_events("Set Overtemperature Alarm Action")

    def get_overtemperature_alarm_action(self) -> AlarmAction:
        return AlarmAction(self._query("SYSTem:ALARm:ACTion:OTEMperature?").strip())

    # ------------------------------------------------------------------
    # Raw SCPI escape hatch (task §10)
    # ------------------------------------------------------------------
    def enable_raw_scpi(self, confirmation: str) -> None:
        if confirmation != _RAW_SCPI_CONFIRMATION:
            raise EaPs9000TValidationError(
                f'raw SCPI requires the exact confirmation text "{_RAW_SCPI_CONFIRMATION}"'
            )
        self._raw_scpi_enabled = True

    def _require_raw_scpi_enabled(self) -> None:
        if not self._raw_scpi_enabled:
            raise EaPs9000TValidationError(
                "raw SCPI is disabled; call enable_raw_scpi() with the exact confirmation text first"
            )

    def raw_query(self, command: str) -> str:
        self._require_raw_scpi_enabled()
        return self._query(command)

    def raw_write(self, command: str) -> None:
        self._require_raw_scpi_enabled()
        self._write(command)
