import json

import bk8500b.cli as cli
from bk8500b import Measurement, Protocol
from bk8500b.measurements import InstrumentIdentity
from bk8500b.status import DiagnosticSnapshot, MeasurementSnapshot
from bk8500b.enums import SessionState
from bk8500b.transport import PortInfo
from datetime import datetime, timezone


class FakeDevice:
    def __init__(self, config):
        self.config = config
    def __enter__(self): return self
    def __exit__(self, *args): return None
    def identify(self): return InstrumentIdentity("B&K", "8500B", "123", "1", "raw")
    def measure_all(self):
        m = lambda v,u: Measurement.now(v,u,Protocol.SCPI)
        return MeasurementSnapshot(m(1,"V"), m(2,"A"), m(2,"W"), m(0.5,"ohm"), None)
    def diagnostic_snapshot(self):
        return DiagnosticSnapshot(datetime.now(timezone.utc), SessionState.CONNECTED_READY, Protocol.SCPI, True, self.identify(), None, None, {}, False, ())


def test_cli_list_ports(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "list_serial_ports", lambda: (PortInfo("COM1", "fake"),))
    assert cli.main(["list-ports"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data[0]["device"] == "COM1"


def test_cli_commands(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "BK8500B", FakeDevice)
    for command in ("identify", "measure", "diagnostic"):
        assert cli.main([command, "--port", "COM1"]) == 0
        assert capsys.readouterr().out.strip()


def test_cli_error(monkeypatch, capsys) -> None:
    class Broken:
        def __init__(self, config): raise RuntimeError("boom")
    monkeypatch.setattr(cli, "BK8500B", Broken)
    assert cli.main(["identify", "--port", "COM1"]) == 2
    assert "boom" in capsys.readouterr().err
