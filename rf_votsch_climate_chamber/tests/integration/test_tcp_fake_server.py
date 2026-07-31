"""Real TCP-boundary integration test using the deterministic fake chamber."""
from __future__ import annotations

from rf_votsch_climate_chamber.library import VotschClimateChamberLibrary
from tests.support.fake_chamber import FakeChamberServer


def test_tcp_connect_query_set_and_disconnect(tmp_path) -> None:
    server = FakeChamberServer().start()
    library = VotschClimateChamberLibrary(managed_configuration_root=str(tmp_path / "profiles"))
    try:
        state = library.connect(
            f"tcp://127.0.0.1:{server.port}",
            timeout_s=0.5,
            response_timeout_s=0.5,
            temperature_min_c=-40,
            temperature_max_c=180,
        )
        assert state["connected"] is True
        assert "FAKE-2601" in library.get_identity()
        library.set_temperature(30)
        assert library.get_temperature_setpoint() == 30.0
    finally:
        try:
            library.disconnect_all()
        finally:
            server.stop()
