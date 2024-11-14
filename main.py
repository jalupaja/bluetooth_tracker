from db import Exporter
from bluetooth_scanner import BluetoothScanner
from ble_scanner import BleScanner
import log

if __name__ == "__main__":
    exporter = Exporter("db.db")
    bluetooth_scanner = BluetoothScanner(exporter)
    ble_scanner = BleScanner(exporter)

    bluetooth_scanner.start_scanning()
    # Start scanning
    ble_scanner.start_scanning()

    exporter.start_exporting()

    try:
        while True:
            input("Press Enter to stop scanning...\n")
            bluetooth_scanner.stop_scanning()
            ble_scanner.stop_scanning()
            break
    except KeyboardInterrupt:
        # Handle Ctrl+C
        log.debug("\nScanning interrupted by user.")
        bluetooth_scanner.stop_scanning()
        ble_scanner.stop_scanning()

    exporter.stop_exporting()

