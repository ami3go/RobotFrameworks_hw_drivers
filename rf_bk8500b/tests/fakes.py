from __future__ import annotations

from collections import deque
import threading

from bk8500b.exceptions import ReadTimeoutError, WriteTimeoutError


class FakeSCPITransport:
    def __init__(self) -> None:
        self._open = False
        self.responses: deque[bytes] = deque()
        self.writes: list[bytes] = []
        self.lock = threading.Lock()
        self.fail_write_for: set[str] = set()
        self.fail_read_count = 0
        self.state: dict[str, str] = {
            "INPut": "0",
            "INPut:SHORt": "0",
            "FUNCtion": "CURRent",
            "CURRent": "0.1",
            "VOLTage": "5",
            "POWer": "1",
            "RESistance": "100",
            "CURRent:RANGe": "30",
            "VOLTage:RANGe": "150",
            "VOLTage:RANGe:AUTO": "1",
            "CURRent:SLEW": "1",
            "CURRent:SLEW:RISE": "1",
            "CURRent:SLEW:FALL": "1",
            "SYSTem:SENSe": "0",
            "VOLTage:ON": "1",
            "VOLTage:OFF": "0.5",
            "*ESE": "0",
            "*PSC": "1",
            "*SRE": "0",
            "STATus:QUEStionable:ENABle": "0",
            "STATus:OPERation:ENABle": "0",
            "DYNamic:HIGH": "1",
            "DYNamic:HIGH:DWELl": "0.01",
            "DYNamic:LOW": "0.1",
            "DYNamic:LOW:DWELl": "0.01",
            "DYNamic:SLEW": "1",
            "DYNamic:MODE": "CONTinuous",
            "LED:VOLTage": "18",
            "LED:CURRent": "0.35",
            "LED:RCOeff": "0.2",
        }
        self.error_queue: deque[str] = deque()
        self.identity_response = "B&K Precision,BK8500B,SN123,1.45"

    @property
    def is_open(self) -> bool:
        return self._open

    def open(self) -> None:
        self._open = True

    def close(self) -> None:
        self._open = False

    def write(self, data: bytes, *, timeout_s: float | None = None) -> int:
        if not self._open:
            raise RuntimeError("not open")
        text = data.decode("ascii").strip()
        with self.lock:
            self.writes.append(data)
        if text in self.fail_write_for:
            raise WriteTimeoutError("injected write timeout")
        self._handle(text)
        return len(data)

    def _handle(self, text: str) -> None:
        if text == "*IDN?":
            self.responses.append((self.identity_response + "\n").encode())
            return
        fixed = {
            "SYSTem:VERSion?": "1999.0",
            "*STB?": "0",
            "*ESR?": "0",
            "*OPC?": "1",
            "*TST?": "0",
            "STATus:QUEStionable:EVENt?": "0",
            "STATus:QUEStionable:CONDition?": "0",
            "STATus:OPERation:EVENt?": "0",
            "STATus:OPERation:CONDition?": "0",
            "MEASure:VOLTage?": "12.0",
            "MEASure:VOLTage:MAXimum?": "12.1",
            "MEASure:VOLTage:MINimum?": "11.9",
            "MEASure:VOLTage:PTPeak?": "0.2",
            "MEASure:CURRent?": "1.0",
            "MEASure:CURRent:MAXimum?": "1.1",
            "MEASure:CURRent:MINimum?": "0.9",
            "MEASure:CURRent:PTPeak?": "0.2",
            "MEASure:POWer?": "12.0",
            "MEASure:RESistance?": "12.0",
            "PEAK:VOLTage:MAXimum?": "12.2",
            "PEAK:VOLTage:MINimum?": "11.8",
            "PEAK:CURRent:MAXimum?": "1.2",
            "PEAK:CURRent:MINimum?": "0.8",
            "TIME:VOLTage:UP?": "0.002",
            "TIME:VOLTage:DOWN?": "0.003",
            "TIMing:RESult?": "0.004",
            "OCP:RESult?": "4.68",
            "OCP:RESult:PMAX?": "55.34,11.8,4.69",
        }
        if text in fixed:
            self.responses.append((fixed[text] + "\n").encode())
            return
        if text == "SYSTem:ERRor?":
            response = self.error_queue.popleft() if self.error_queue else '0,"No Error"'
            self.responses.append((response + "\n").encode())
            return
        if text.endswith("?"):
            key = text[:-1]
            if key in self.state:
                self.responses.append((self.state[key] + "\n").encode())
                return
            self.responses.append(b"0\n")
            return
        if text in {"*CLS", "*RST", "*TRG", "PROTection:CLEar", "SYSTem:LOCal", "SYSTem:REMote", "SYSTem:RWLock"}:
            if text == "*RST":
                self.state["INPut"] = "0"
            return
        if text.startswith("*SAV ") or text.startswith("*RCL "):
            return
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            key, value = parts
            aliases = {
                "MODE": "FUNCtion",
                "SOURce:FUNCtion": "FUNCtion",
            }
            key = aliases.get(key, key)
            if value.upper() in {"ON", "OFF"}:
                value = "1" if value.upper() == "ON" else "0"
            self.state[key] = value
            return
        raise AssertionError(f"Unhandled fake SCPI command: {text}")

    def read(self, size: int, *, timeout_s: float | None = None) -> bytes:
        if self.fail_read_count:
            self.fail_read_count -= 1
            raise ReadTimeoutError("injected read timeout")
        if not self.responses:
            raise ReadTimeoutError("no response")
        value = self.responses[0]
        chunk = value[:size]
        remainder = value[size:]
        if remainder:
            self.responses[0] = remainder
        else:
            self.responses.popleft()
        return chunk

    def read_until(self, terminator: bytes, *, maximum_bytes: int, timeout_s: float | None = None) -> bytes:
        if self.fail_read_count:
            self.fail_read_count -= 1
            raise ReadTimeoutError("injected read timeout")
        if not self.responses:
            raise ReadTimeoutError("no response")
        value = self.responses.popleft()
        if len(value) > maximum_bytes:
            raise RuntimeError("oversized")
        return value

    def reset_input_buffer(self) -> None:
        self.responses.clear()

    def reset_output_buffer(self) -> None:
        return None
