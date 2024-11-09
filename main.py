from db import Exporter
from bluetooth_scanner import BluetoothScanner
from ble_scanner import BleScanner
import log

if __name__ == "__main__":
    exporter = Exporter("db.db")
    bluetooth_scanner = BluetoothScanner(exporter)
    ble_scanner = BleScanner(exporter)

    # Start scanning in the background
    bluetooth_scanner.start_scanning()
    ble_scanner.start_scanning()

    exporter.start_exporting()

    try:
        while True:
            # Wait for the user to press 'Enter' to stop scanning
            input("Press Enter to stop scanning...\n")
            bluetooth_scanner.stop_scanning()
            ble_scanner.stop_scanning()
            break
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        log.debug("\nScanning interrupted by user.")
        bluetooth_scanner.stop_scanning()
        ble_scanner.stop_scanning()

    exporter.stop_exporting()

