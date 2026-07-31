from bk8500b.transport import list_serial_ports

for port in list_serial_ports():
    print(port.device, port.description or "", port.hardware_id or "")
