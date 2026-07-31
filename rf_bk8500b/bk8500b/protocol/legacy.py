"""Legacy frame transaction engine.

Stable public use is intentionally restricted to raw transactions and pure frame
codec operations until hardware captures resolve response status-byte placement.
"""
from __future__ import annotations

import time

from ..config import DriverConfig
from ..enums import RiskClass
from ..exceptions import FrameSyncError, ReadTimeoutError, UnsupportedFeatureError
from ..execution import CommandExecutor
from .legacy_codec import FRAME_LENGTH, START_BYTE, LegacyFrame, build_frame, decode_frame


class LegacyProtocol:
    def __init__(self, config: DriverConfig, executor: CommandExecutor) -> None:
        self.config = config
        self.executor = executor

    def _read_frame(self, timeout_s: float) -> bytes:
        deadline = time.monotonic() + timeout_s
        buffer = bytearray()
        while time.monotonic() < deadline:
            remaining = max(0.001, deadline - time.monotonic())
            try:
                byte = self.executor.transport.read(1, timeout_s=remaining)
            except ReadTimeoutError:
                break
            if not buffer and byte[0] != START_BYTE:
                continue
            buffer += byte
            if len(buffer) == FRAME_LENGTH:
                return bytes(buffer)
        if buffer:
            raise FrameSyncError("Partial legacy frame received", context={"received": len(buffer)})
        raise ReadTimeoutError("Legacy frame was not received before deadline")

    def transact(
        self,
        frame: bytes,
        *,
        operation: str = "legacy.raw",
        timeout_s: float | None = None,
        retryable: bool = False,
        destructive_read: bool = False,
    ) -> LegacyFrame:
        request = decode_frame(frame)
        response = self.executor.query(
            frame,
            operation=operation,
            read_response=self._read_frame,
            validate_response=lambda raw: decode_frame(raw, expected_address=request.address),
            timeout_s=timeout_s,
            retryable=retryable,
            destructive_read=destructive_read,
        )
        return response

    def read_ratings_experimental(self) -> LegacyFrame:
        frame = build_frame(self.config.address, 0x01)
        return self.transact(frame, operation="legacy.read_ratings", retryable=True)

    def stable_command(self, *args, **kwargs):
        raise UnsupportedFeatureError(
            "Stable legacy high-level commands are blocked pending HIL evidence for response layout"
        )
