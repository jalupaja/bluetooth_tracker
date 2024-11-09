from bleak import BleakScanner, BleakClient
import threading
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from bluetooth_device import BluetoothDevice

from ble_device import BleDevice
from db import Exporter
import log

class BleScanner:
    def __init__(self, exporter: Exporter):
        self.exporter = exporter
        self.scanning = True
        self.devices = []
        self.executor = ThreadPoolExecutor(max_workers=10)

    def get_device_info(self, device):
        log.debug(f"Fetching detailed information for BLE device: {device.address}")
        # TODO implement? needed?

    def scan_ble_devices(self):
        log.debug("Scanning for BLE devices...")

        # try:
        devices = asyncio.run(BleakScanner.discover())
        # except: # TODO what if ble is off
            # log.debug(f"Discovery failed: {e}")
            # time.sleep(1)
            # continue

        if devices:
            log.debug(f"Found {len(devices)} BLE device(s):")
            for d in devices:
                device = BleDevice(d)
                self.devices.append(device)
                log.info(f"BLE Device Address: {device.address} | Device Name: {device.name}")
                self.exporter.add_ble_devices(device)
        else:
            log.debug("No BLE devices found.")

        # TODO
        time.sleep(3)

    def start_scanning(self):
        scan_thread = threading.Thread(target=self.scan_ble_devices)
        scan_thread.daemon = True
        scan_thread.start()

    def stop_scanning(self):
        self.scanning = False
        log.debug("BLE Scanning stopped.")

