"""Strict parsers for documented 34970A/34972A ASCII responses."""
from __future__ import annotations

import csv
import io
import re

from ..exceptions import DriverResponseError
from ..models import InstrumentIdentity, ModuleInfo

SUPPORTED_MODELS = {"34970A", "34972A"}
SUPPORTED_MODULES = {"0", "34901A", "34902A", "34903A", "34904A", "34905A", "34906A", "34907A", "34908A"}


def _split_csv(raw: str) -> list[str]:
    try:
        row = next(csv.reader(io.StringIO(raw.strip()), skipinitialspace=True))
    except Exception as exc:
        raise DriverResponseError(f"malformed comma-separated response: {raw!r}") from exc
    return [item.strip() for item in row]


def parse_identity(raw: str) -> InstrumentIdentity:
    fields = _split_csv(raw)
    if len(fields) != 4:
        raise DriverResponseError(f"identity response must contain 4 fields, got {len(fields)}: {raw!r}")
    manufacturer, model, serial, firmware = fields
    if model not in SUPPORTED_MODELS:
        raise DriverResponseError(f"unsupported instrument model in identity response: {model!r}")
    if not manufacturer or not firmware:
        raise DriverResponseError(f"identity response contains empty required fields: {raw!r}")
    return InstrumentIdentity(manufacturer, model, serial, firmware, raw.strip())


def parse_module_identity(slot: int, raw: str) -> ModuleInfo:
    fields = _split_csv(raw)
    if len(fields) != 4:
        raise DriverResponseError(f"module response must contain 4 fields, got {len(fields)}: {raw!r}")
    manufacturer, model, serial, firmware = fields
    model = model.upper()
    if model not in SUPPORTED_MODULES:
        raise DriverResponseError(f"unexpected module model {model!r} in slot {slot}")
    return ModuleInfo(slot, manufacturer, model, serial, firmware, raw.strip())


_ERROR_RE = re.compile(r'^\s*([+-]?\d+)\s*,\s*"((?:[^"\\]|\\.)*)"\s*$')


def parse_device_error(raw: str) -> dict[str, object]:
    match = _ERROR_RE.fullmatch(raw)
    if not match:
        raise DriverResponseError(f"malformed SYST:ERR? response: {raw!r}")
    return {
        "code": int(match.group(1)),
        "message": match.group(2),
        "raw": raw.strip(),
        "source": "device",
    }
