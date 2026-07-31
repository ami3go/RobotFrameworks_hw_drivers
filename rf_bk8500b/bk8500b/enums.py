"""Public enumerations for the B&K 8500B driver."""
from __future__ import annotations

from enum import Enum, IntFlag, auto


class Protocol(str, Enum):
    SCPI = "scpi"
    LEGACY = "legacy"
    AUTO = "auto"


class OperatingMode(str, Enum):
    CURRENT = "CURRent"
    VOLTAGE = "VOLTage"
    POWER = "POWer"
    RESISTANCE = "RESistance"
    DYNAMIC = "DYNamic"
    LED = "LED"
    IMPEDANCE = "IMPedance"

    @property
    def scpi_token(self) -> str:
        return self.value

    @classmethod
    def from_response(cls, value: str) -> "OperatingMode":
        token = value.strip().upper()
        aliases = {
            "CURR": cls.CURRENT,
            "CURRENT": cls.CURRENT,
            "CC": cls.CURRENT,
            "VOLT": cls.VOLTAGE,
            "VOLTAGE": cls.VOLTAGE,
            "CV": cls.VOLTAGE,
            "POW": cls.POWER,
            "POWER": cls.POWER,
            "CW": cls.POWER,
            "CP": cls.POWER,
            "RES": cls.RESISTANCE,
            "RESISTANCE": cls.RESISTANCE,
            "CR": cls.RESISTANCE,
            "DYN": cls.DYNAMIC,
            "DYNAMIC": cls.DYNAMIC,
            "LED": cls.LED,
            "IMP": cls.IMPEDANCE,
            "IMPEDANCE": cls.IMPEDANCE,
        }
        try:
            return aliases[token]
        except KeyError as exc:
            raise ValueError(f"Unknown operating mode response: {value!r}") from exc


class DynamicMode(str, Enum):
    CONTINUOUS = "CONTinuous"
    PULSE = "PULSe"
    TOGGLE = "TOGGLe"


class TriggerSource(str, Enum):
    MANUAL = "MANual"
    EXTERNAL = "EXTernal"
    BUS = "BUS"
    HOLD = "HOLD"
    VOLTAGE = "VOLTage"
    CURRENT = "CURRent"


class TriggerEdge(str, Enum):
    RISE = "RISE"
    FALL = "FALL"


class SessionState(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    IDENTIFYING = "identifying"
    CONNECTED_UNSYNCHRONIZED = "connected_unsynchronized"
    CONNECTED_READY = "connected_ready"
    DEGRADED = "degraded"
    RECONNECTING = "reconnecting"
    CLOSING = "closing"
    FAILED = "failed"


class CommandOutcome(str, Enum):
    CREATED = "created"
    VALIDATED = "validated"
    WAITING_FOR_LOCK = "waiting_for_lock"
    WRITING = "writing"
    WRITE_COMPLETE = "write_complete"
    READING = "reading"
    RESPONSE_VALIDATED = "response_validated"
    COMPLETED = "completed"
    CANCELLED_NOT_SENT = "cancelled_not_sent"
    FAILED_NOT_SENT = "failed_not_sent"
    RETRYABLE_READ_FAILURE = "retryable_read_failure"
    OUTCOME_INDETERMINATE = "outcome_indeterminate"
    PROTOCOL_FAILURE = "protocol_failure"
    DEVICE_REJECTED = "device_rejected"


class LongOperationState(str, Enum):
    IDLE = "idle"
    CONFIGURING = "configuring"
    ARMED = "armed"
    RUNNING = "running"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    OUTCOME_INDETERMINATE = "outcome_indeterminate"
    FAILED = "failed"


class ProtectionFlag(IntFlag):
    NONE = 0
    REVERSE_VOLTAGE = auto()
    OVER_VOLTAGE = auto()
    OVER_CURRENT = auto()
    OVER_POWER = auto()
    OVER_TEMPERATURE = auto()
    REMOTE_SENSE_DISCONNECTED = auto()
    UNREGULATED = auto()


class RiskClass(str, Enum):
    READ_ONLY = "read_only"
    CONFIGURATION = "configuration"
    HAZARDOUS = "hazardous"
    NON_IDEMPOTENT = "non_idempotent"
