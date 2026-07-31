from __future__ import annotations
import socket
import pytest
from rf_votsch_climate_chamber.converters import (
    normalize_alias, sanitize, to_bool, to_float, to_int,
    to_nonnegative_seconds, to_positive_seconds,
)
from rf_votsch_climate_chamber.exceptions import (
    DriverError, DriverProtocolError,
    DriverTimeoutError, DriverTransportOpenError,
)
from rf_votsch_climate_chamber.core import ClimateChamberCore
from rf_votsch_climate_chamber.transports.simulator import SimulatorTransport
from rf_votsch_climate_chamber.transports.tcp import TcpTransport
from rf_votsch_climate_chamber.transports.models import ReadRequest, ReplayPolicy

@pytest.mark.parametrize(('value','expected'), [('true',True),('OFF',False),(1,True),(0,False),(True,True)])
def test_to_bool(value, expected): assert to_bool(value,'x') is expected

def test_converters_reject_and_convert():
    assert to_float('3.5','x') == 3.5
    assert to_int('3','x',minimum=1) == 3
    assert to_positive_seconds('500 milliseconds','x') == pytest.approx(0.5)
    assert to_nonnegative_seconds('0 seconds','x') == 0
    assert normalize_alias(' Main ') == 'main'
    assert sanitize({1:b'abc'}) == {'1':'abc'}
    with pytest.raises(Exception): to_bool('maybe','x')
    with pytest.raises(Exception): to_float(True,'x')
    with pytest.raises(Exception): to_int(0,'x',minimum=1)
    with pytest.raises(Exception): to_positive_seconds(0,'x')


def test_driver_error_schema():
    cause=ValueError('bad')
    error=DriverError('failed', operation='test', details={'x':1}, cause=cause)
    data=error.to_dict()
    assert data['code'].startswith('RFDS-')
    assert data['operation'] == 'test'
    assert 'failed' in error.to_robot_message()


def test_simulator_protocol_faults_and_recovery():
    transport=SimulatorTransport('faults')
    core=ClimateChamberCore(transport, query_retries=0)
    core.connect()
    transport.simulator_state.fault_mode='malformed'
    with pytest.raises(DriverProtocolError): core.get_status()
    assert core.get_status() == 'READY'
    transport.simulator_state.fault_mode='timeout'
    with pytest.raises(DriverTimeoutError): core.measure_temperature_c()
    assert core.measure_temperature_c() == 25.0
    core.disconnect()


class FakeSocket:
    def __init__(self, chunks):
        self.chunks=list(chunks); self.sent=[]; self.timeout=None; self.closed=False
    def settimeout(self,value): self.timeout=value
    def setsockopt(self,*args): pass
    def sendall(self,data): self.sent.append(data)
    def recv(self,size):
        del size
        if not self.chunks: raise socket.timeout()
        value=self.chunks.pop(0)
        if isinstance(value,BaseException): raise value
        return value
    def shutdown(self,how): pass
    def close(self): self.closed=True


def test_tcp_transport_preserves_extra_frame_bytes():
    fake=FakeSocket([b'1\xb6A\r1\xb6B\r'])
    transport=TcpTransport('example',2049,timeout_s=0.1,socket_factory=lambda endpoint,timeout: fake)
    transport.open()
    first=transport.transact(b'Q1\r',ReadRequest(),timeout_s=0.1,replay_policy=ReplayPolicy.SAFE_QUERY,operation_id='one')
    second=transport.transact(b'Q2\r',ReadRequest(),timeout_s=0.1,replay_policy=ReplayPolicy.SAFE_QUERY,operation_id='two')
    assert first == b'1\xb6A\r'
    assert second == b'1\xb6B\r'
    transport.close(); assert fake.closed


def test_tcp_open_failure_is_typed():
    def fail(endpoint, timeout): raise OSError('offline')
    transport=TcpTransport('offline',socket_factory=fail)
    with pytest.raises(DriverTransportOpenError): transport.open()

def test_suite_listener_cleanup_is_best_effort():
    from rf_votsch_climate_chamber.lifecycle import SuiteLifecycleListener
    class Registry:
        def __init__(self): self.called=False
        def disconnect_all(self, **kwargs): self.called=True
    registry=Registry(); listener=SuiteLifecycleListener(registry)
    listener.end_suite(None, None)
    assert registry.called is True
    class Failing:
        def disconnect_all(self, **kwargs): raise RuntimeError('cleanup')
    SuiteLifecycleListener(Failing()).end_suite(None, None)
