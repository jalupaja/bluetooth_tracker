from lib.db import BluetoothDatabase, Exporter
from lib.bt_scanner import bt_scanner
from lib.ble_scanner import ble_scanner
from lib.ble_device import ble_device
from lib.log import log

def ble_callback(device, _):
    print(f"found device: {device.address} {device.name}")
    db.insert_ble_device(ble_device(device))

if __name__ == "__main__":
    db_path = "db.db"
    db = BluetoothDatabase(db_path)
    exporter = Exporter(db_path)
    bt_scanr = bt_scanner(exporter)
    ble_scanr = ble_scanner(ble_callback)

    # Start scanning
    ble_scanr.scan()
    bt_scanr.start_scanning()

    exporter.start_exporting()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        # Handle Ctrl+C
        log.debug("\nScanning interrupted by user.")
        bt_scanr.stop_scanning()
        ble_scanr.stop()

    exporter.stop_exporting()

