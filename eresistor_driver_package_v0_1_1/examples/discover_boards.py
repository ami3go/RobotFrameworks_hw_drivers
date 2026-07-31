from eresistor_driver import discover_boards

boards = discover_boards("192.168.7.0/24")

# discover_boards() returns list[BoardInfo].
# You can index it and use simple aliases such as .ip and .fw.
if boards:
    print("First board IP:", boards[0].ip)
    print("First board firmware:", boards[0].fw)

for board in boards:
    print(f"{board.ip} serial={board.serial} fw={board.fw} model={board.model} http={board.http_ok} scpi={board.scpi_ok}")
