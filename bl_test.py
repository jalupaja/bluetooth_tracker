import sys
from PyQt6.QtCore import QCoreApplication, QObject, pyqtSlot
from PyQt6.QtBluetooth import QBluetoothDeviceDiscoveryAgent, QBluetoothDeviceInfo


class BluetoothScanner(QObject):
    devices = []

    def __init__(self):
        super().__init__()
        self.discovery_agent = QBluetoothDeviceDiscoveryAgent()
        self.discovery_agent.deviceDiscovered.connect(self.device_discovered)
        self.discovery_agent.finished.connect(self.scan_finished)

    @pyqtSlot()
    def start_scan(self):
        print("Scanning for Bluetooth devices...")
        self.discovery_agent.start()

    @pyqtSlot(QBluetoothDeviceInfo)
    def device_discovered(self, device_info):
        print(
            f"Found device: {device_info.name()} - {device_info.address().toString()}"
        )
        self.devices.append(device_info)

    @pyqtSlot()
    def scan_finished(self):
        print("Scan finished.")
        QCoreApplication.quit()


scanner = None

if __name__ == "__main__":
    app = QCoreApplication(sys.argv)
    scanner = BluetoothScanner()
    scanner.start_scan()
    app.exec()
