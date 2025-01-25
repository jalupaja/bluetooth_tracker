from bleak import BleakScanner, BleakClient
import threading
import time
import asyncio

from lib.ble_device import ble_device
from lib.log import log

from concurrent.futures import ThreadPoolExecutor

class ble_scanner:
    MAX_CONNECTION_TRIES = 3
    callback = None
    uuids = None
    gatt_executor = ThreadPoolExecutor(10)
    finished_gatts = set()
    gatt_tries = {}

    def __init__(self, callback):
        self.callback = callback
        self.loop = None

    async def _scan(self):
        if self.uuids:
            scanner = BleakScanner(self.scanner_callback, uuids=self.uuids)
        else:
            scanner = BleakScanner(self.scanner_callback)

        try:
            while True:
                await scanner.start()
                await asyncio.sleep(1)
                await scanner.stop()
        except asyncio.CancelledError:
            pass
        finally:
            await scanner.stop()

    def scanner_callback(self, device, advertisement_data):
        if device.address in self.finished_gatts:
            self.callback(device, None)
        else:
            self.finished_gatts.add(device.address)
            self.gatt_executor.submit(self.connect_gatt, device)

    def connect_gatt(self, device):
        async def run(address):
            log.info(f"Connecting to {address}")
            try:
                async with BleakClient(address) as client:
                    if not client.is_connected:
                        return None
                    gatt_services = []
                    for service in client.services:
                        characteristics = []
                        for char in service.characteristics:
                            saved_char = GattCharacteristic(char)
                            characteristics.append(saved_char)

                            try:
                                if 'read' in char.properties:
                                    saved_char.value = await client.read_gatt_char(char.uuid)
                            except Exception as e:
                                if not client.is_connected:
                                    client.connect()

                        gatt_services.append(GattService(service, characteristics))
                    log.debug(f"Successfully connected to {address}")
                    return gatt_services
            except Exception as e:
                log.debug(f"Error connecting to {address}: {e}")
                # allow more tries because it failed unexpectedly
                if not address in self.gatt_tries:
                    self.gatt_tries[address] = 0
                self.gatt_tries[address] += 1

                if self.gatt_tries[address] <= self.MAX_CONNECTION_TRIES:
                    self.finished_gatts.remove(address) # retry
                return None

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        services = loop.run_until_complete(run(device.address))
        self.callback(device, services)

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
            asyncio.run_coroutine_threadsafe(self._shutdown_loop(self.loop), self.loop)

    async def _shutdown_loop(self, loop):
        for task in asyncio.all_tasks(loop):
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self.gatt_executor.shutdown(wait=True)

        loop.stop()

class GattService:
    def __init__(self, service, characteristics):
        self.description = service.description
        self.handle = service.handle
        self.uuid = service.uuid
        self.characteristics = characteristics

    def __str__(self):
        ret = f"{self.uuid}: {self.description} ({self.handle}):\n"
        for char in self.characteristics:
            ret += f"\t{char}\n"
        return ret

class GattCharacteristic:
    def __init__(self, char):
        self.description = char.description
        self.handle = char.handle
        self.properties = char.properties
        self.uuid = char.uuid
        self.value = None

    def __str__(self):
        return f"{self.uuid}: {self.description} ({self.handle}): {', '.join(self.properties)} = {self.value}"

