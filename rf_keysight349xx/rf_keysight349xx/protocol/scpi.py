"""ASCII SCPI protocol adapter over the byte-oriented transport."""
from __future__ import annotations

from ..exceptions import DriverConnectionError, DriverProtocolError, DriverTimeoutError
from ..transports.base import ReadRequest, ReplayPolicy


class ScpiProtocol:
    encoding = "ascii"
    terminator = b"\n"
    max_response_bytes = 1024 * 1024

    def __init__(self, transport) -> None:
        self.transport = transport

    def _encode(self, command: str) -> bytes:
        if not isinstance(command, str):
            raise TypeError("SCPI command must be str")
        command = command.rstrip("\r\n")
        try:
            return command.encode(self.encoding, errors="strict") + self.terminator
        except UnicodeEncodeError as exc:
            raise DriverProtocolError("SCPI command contains non-ASCII data") from exc

    def write(self, command: str, *, timeout_s: float, operation_id: str) -> None:
        try:
            self.transport.write(self._encode(command), timeout_s=timeout_s, operation_id=operation_id)
        except TimeoutError as exc:
            raise DriverTimeoutError(f"timeout writing SCPI command {command!r}", operation=operation_id) from exc
        except DriverProtocolError:
            raise
        except Exception as exc:
            raise DriverConnectionError(f"transport write failed for {command!r}", operation=operation_id) from exc

    def query(self, command: str, *, timeout_s: float, operation_id: str) -> str:
        request = ReadRequest(
            maximum_length=self.max_response_bytes,
            terminator=self.terminator,
            include_terminator=False,
            allow_empty=False,
        )
        try:
            data = self.transport.transact(
                self._encode(command),
                request,
                timeout_s=timeout_s,
                replay_policy=ReplayPolicy.IF_IDEMPOTENT,
                operation_id=operation_id,
            )
        except TimeoutError as exc:
            raise DriverTimeoutError(f"timeout querying SCPI command {command!r}", operation=operation_id, retryable=True) from exc
        except (DriverProtocolError, DriverTimeoutError):
            raise
        except Exception as exc:
            raise DriverConnectionError(f"transport transaction failed for {command!r}", operation=operation_id) from exc
        try:
            text = data.decode(self.encoding, errors="strict").strip()
        except UnicodeDecodeError as exc:
            raise DriverProtocolError("SCPI response is not valid ASCII", operation=operation_id) from exc
        if text == "":
            raise DriverProtocolError("SCPI query returned an empty response", operation=operation_id)
        return text
