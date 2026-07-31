from eresistor_driver import BoardInfo


def test_board_info_alias_properties():
    board = BoardInfo(
        host="192.168.1.50",
        serial="E66178758B4A872A",
        firmware_version="0.4.0",
        idn="OpenBench,E-Resistor,E66178758B4A872A,0.4.0",
        http_ok=True,
        scpi_ok=True,
    )

    assert board.ip == "192.168.1.50"
    assert board.address == "192.168.1.50"
    assert board.fw == "0.4.0"
    assert board.firmware == "0.4.0"
    assert board.version == "0.4.0"
    assert board.serial_number == "E66178758B4A872A"
    assert board.manufacturer == "OpenBench"
    assert board.vendor == "OpenBench"
    assert board.model == "E-Resistor"
    assert board.product == "E-Resistor"
    assert board.scpi_address == "192.168.1.50:5025"
    assert board.http_url == "http://192.168.1.50/"
    assert board.as_dict()["ip"] == "192.168.1.50"
    assert board.as_dict()["fw"] == "0.4.0"
