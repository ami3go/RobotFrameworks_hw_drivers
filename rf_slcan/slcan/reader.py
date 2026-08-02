"""The background reader thread — new architecture for this repo.

Every other driver here is pure query/response: write a command, read
exactly the one line that answers it. SLCAN can't work that way because the
adapter may push a received-frame notification onto the same serial line at
any moment, including between a command and its own acknowledgement. This
module is the single place that owns that complexity: one daemon thread
continuously reads lines and routes each one to either ``rx_queue`` (an
unsolicited CAN frame) or ``ack_queue`` (the result of whatever command is
currently in flight — an ack, a nack, or a status/version/serial query's
data), so ``driver.py`` and ``codec.py`` never have to reason about timing.
"""

from __future__ import annotations

import queue
import threading

from . import codec
from .exceptions import SlcanError, SlcanTimeoutError
from .models import CanFrame
from .transport import Transport

_POLL_TIMEOUT_S = 0.2
_MAX_LINE_BYTES = 64
DEFAULT_RX_QUEUE_MAXSIZE = 1000

FAULT_SENTINEL = object()
"""Pushed to ``ack_queue`` when the reader thread dies, so a command
currently blocked on ``ack_queue.get()`` wakes up instead of hanging until
its own timeout."""


class BackgroundReader:
    def __init__(self, transport: Transport, *, rx_queue_maxsize: int = DEFAULT_RX_QUEUE_MAXSIZE) -> None:
        self._transport = transport
        self.ack_queue: queue.Queue[object] = queue.Queue(maxsize=1)
        self.rx_queue: queue.Queue[CanFrame] = queue.Queue(maxsize=rx_queue_maxsize)
        self.overflow_count = 0
        self.fault: Exception | None = None
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="slcan-reader", daemon=True)
        self._thread.start()

    def stop(self, timeout_s: float = 2.0) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout_s)
        self._thread = None

    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # -- the loop --------------------------------------------------------
    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                raw = self._transport.read_until(
                    codec.TERMINATORS, maximum_bytes=_MAX_LINE_BYTES, timeout_s=_POLL_TIMEOUT_S
                )
            except SlcanTimeoutError:
                continue  # just a quiet bus / idle period; check stop_event and poll again
            except SlcanError as exc:
                self._on_fault(exc)
                return
            except Exception as exc:  # noqa: BLE001 - an unexpected reader failure must
                # surface as a fault on the next call, not vanish with no observer
                self._on_fault(exc)
                return

            try:
                result = codec.classify_line(raw)
            except SlcanError as exc:
                self._on_fault(exc)
                return

            if isinstance(result, CanFrame):
                self._push_frame(result)
            else:
                self._deliver(result)

    def _push_frame(self, frame: CanFrame) -> None:
        try:
            self.rx_queue.put_nowait(frame)
        except queue.Full:
            try:
                self.rx_queue.get_nowait()  # drop oldest to make room
            except queue.Empty:
                pass
            self.overflow_count += 1
            try:
                self.rx_queue.put_nowait(frame)
            except queue.Full:
                pass

    def _deliver(self, result: object) -> None:
        try:
            self.ack_queue.put_nowait(result)
        except queue.Full:
            # A stale, undelivered result from a command that already timed
            # out is sitting here — replace it. driver.py additionally
            # drains this queue before sending a new command, so this is a
            # defensive backstop, not the primary correctness mechanism.
            try:
                self.ack_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.ack_queue.put_nowait(result)
            except queue.Full:
                pass

    def _on_fault(self, exc: Exception) -> None:
        self.fault = exc
        self._deliver(FAULT_SENTINEL)
