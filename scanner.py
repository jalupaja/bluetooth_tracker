from lib.db import BluetoothDatabase
from lib.bt_scanner import bt_scanner
from lib.ble_scanner import ble_scanner
from lib.ble_device import ble_device
from lib.ble_gatt import ble_gatt
from lib.log import log

def ble_callback(device, _):
    dev = ble_device(device)
    gatt.add_possible_device(dev)

    db.insert_ble_device(dev)

def gatt_callback(device, services, characteristics, descriptors):
    db.insert_ble_services(device, services, characteristics, descriptors)

if __name__ == "__main__":
    db_path = "db.db"
    db = BluetoothDatabase(db_path)
    bt_scanr = bt_scanner(db)
    ble_scanr = ble_scanner(ble_callback)
    gatt = ble_gatt(gatt_callback)

    # Start scanning
    ble_scanr.scan()
    bt_scanr.scan()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        # Handle Ctrl+C
        log.debug("\nScanning interrupted by user.")
        ble_scanr.stop()
        bt_scanr.stop()
        gatt.stop()

