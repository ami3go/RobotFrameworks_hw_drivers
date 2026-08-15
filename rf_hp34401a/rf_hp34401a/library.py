"""Final RFDS public facade for the HP 34401A Robot Framework library.

``runtime_library`` contains the cross-cutting runtime/configuration/evidence
corrections. This final layer keeps invalid assertion *configuration* inside
the structured RFDS validation taxonomy while preserving ordinary
``AssertionError`` for a measured DUT value that fails a valid limit.
"""

from __future__ import annotations

import math
from typing import Any

from robot.api.deco import keyword, library

from .converters import as_float
from .exceptions import DriverValidationError
from .legacy_library import _evidenced
from .runtime_library import Hp34401ALibrary as _RuntimeHp34401ALibrary
from .version import __version__


@library(scope="SUITE", auto_keywords=False, version=__version__)
class Hp34401ALibrary(_RuntimeHp34401ALibrary):
    """Effective 26.07 Robot surface with corrected assertion contracts."""

    ROBOT_LIBRARY_SCOPE = "SUITE"
    ROBOT_AUTO_KEYWORDS = False
    ROBOT_LIBRARY_VERSION = __version__

    @keyword("DMM Reading Should Be Between", tags=["rfds:assertion", "rfds:low_risk"])
    @_evidenced
    def dmm_reading_should_be_between(
        self, minimum: object, maximum: object, alias: object | None = None
    ) -> None:
        value, data = self._value_for_assertion(alias)
        low = as_float(minimum, name="minimum")
        high = as_float(maximum, name="maximum")
        if low > high:
            raise DriverValidationError(
                "minimum must be <= maximum",
                operation="DMM Reading Should Be Between",
                alias=data.get("alias"),
            )
        if not low <= value <= high:
            raise AssertionError(
                f"{data['alias']} {data['function']} reading {value} {data['unit']} "
                f"is outside [{low}, {high}]"
            )

    @keyword("DMM Reading Should Be Close To", tags=["rfds:assertion", "rfds:low_risk"])
    @_evidenced
    def dmm_reading_should_be_close_to(
        self,
        expected: object,
        absolute_tolerance: object = 0.0,
        relative_tolerance: object = 0.0,
        alias: object | None = None,
    ) -> None:
        value, data = self._value_for_assertion(alias)
        exp = as_float(expected, name="expected")
        abs_tol = as_float(absolute_tolerance, name="absolute_tolerance")
        rel_tol = as_float(relative_tolerance, name="relative_tolerance")
        if abs_tol < 0 or rel_tol < 0:
            raise DriverValidationError(
                "tolerances must be >= 0",
                operation="DMM Reading Should Be Close To",
                alias=data.get("alias"),
            )
        if not math.isclose(value, exp, rel_tol=rel_tol, abs_tol=abs_tol):
            raise AssertionError(
                f"{data['alias']} {data['function']} reading {value} {data['unit']} "
                f"is not close to {exp}; abs_tol={abs_tol}, rel_tol={rel_tol}"
            )

    @keyword("Stable Resistance Should Be Between", tags=["rfds:assertion", "rfds:low_risk"])
    @_evidenced
    def stable_resistance_should_be_between(
        self, result: dict[str, Any], minimum: object, maximum: object
    ) -> None:
        if not result.get("stable") or result.get("value") is None:
            raise AssertionError(f"Resistance was not stable: {result.get('reason')}")
        low = as_float(minimum, name="minimum")
        high = as_float(maximum, name="maximum")
        if low > high:
            raise DriverValidationError(
                "minimum must be <= maximum",
                operation="Stable Resistance Should Be Between",
            )
        value = float(result["value"])
        if not low <= value <= high:
            raise AssertionError(f"Stable resistance {value} Ohm is outside [{low}, {high}]")


__all__ = ["Hp34401ALibrary"]
