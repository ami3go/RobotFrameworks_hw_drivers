from __future__ import annotations

from collections import deque

from bk8500b.exceptions import ReadTimeoutError
from bk8500b.protocol.legacy_codec import build_frame, decode_frame


class FakeLegacyTransport:
    def __init__(self):
        self._open = False
        self.buffer = deque()
        self.writes = []
    @property
    def is_open(self): return self._open
    def open(self): self._open = True
    def close(self): self._open = False
    def write(self, data: bytes, *, timeout_s=None):
        self.writes.append(data)
        request = decode_frame(data)
        response = build_frame(request.address, request.command, request.payload)
        self.buffer.extend(response)
        return len(data)
    def read(self, size: int, *, timeout_s=None):
        if not self.buffer: raise ReadTimeoutError("empty")
        return bytes(self.buffer.popleft() for _ in range(min(size, len(self.buffer))))
    def read_until(self, *args, **kwargs): raise ReadTimeoutError("not scpi")
    def reset_input_buffer(self): self.buffer.clear()
    def reset_output_buffer(self): pass


class AutoLegacyTransport(FakeLegacyTransport):
    def __init__(self):
        super().__init__()
        self.open_count = 0
        self.scpi_phase = True
    def open(self):
        super().open(); self.open_count += 1
        self.scpi_phase = self.open_count == 1
    def write(self, data: bytes, *, timeout_s=None):
        if self.scpi_phase:
            self.writes.append(data)
            return len(data)
        return super().write(data, timeout_s=timeout_s)
