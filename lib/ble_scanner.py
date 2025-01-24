from bleak import BleakScanner, BleakError, BleakClient
import threading
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

from lib.ble_device import ble_device
from lib.db import Exporter
from lib.log import log

class ble_scanner:
    callback = None
    uuids = None

    def __init__(self, callback):
        self.callback = callback
        self.loop = None

    async def _scan(self):
        if self.uuids:
            scanner = BleakScanner(self.callback, uuids=self.uuids)
        else:
            scanner = BleakScanner(self.callback)

        try:
            while True:
                await scanner.start()
                await asyncio.sleep(1)
                await scanner.stop()
        except asyncio.CancelledError:
            pass
        finally:
            await scanner.stop()

    def scan(self):
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            try:
                self.loop.run_until_complete(self._scan())
            except Exception as e:
                log.error(f"Error in scanning loop: {e}")
            finally:
                self.loop.close()

        t = threading.Thread(target=run_loop, daemon=True)
        t.start()

    def stop(self):
        if self.loop:
            asyncio.run_coroutine_threadsafe(self._shutdown_loop(), self.loop)

    async def _shutdown_loop(self):
        for task in asyncio.all_tasks(self.loop):
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self.loop.stop()


class ble_scanner2:
    def __init__(self, exporter: Exporter):
        self.exporter = exporter
        self.scanning = True
        self.devices = []
        self.executor = ThreadPoolExecutor(max_workers=10)

    def get_device_info(self, device):
        log.debug(f"Fetching detailed information for BLE device: {device.address}")
        # TODO implement? needed?

    def scan_ble_devices(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while self.scanning:
            log.debug("Scanning for BLE devices...")

            try:
              devices = loop.run_until_complete(BleakScanner.discover())
            except BleakError as e:
                log.warning(f"Discovery failed: {e}")
                time.sleep(1)
                continue

            if devices:
                log.debug(f"Found {len(devices)} BLE device(s):")
                for d in devices:
                    device = ble_device(d)
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

