from bleak import BleakScanner, BleakClient
import threading
import time
import asyncio

from lib.ble_device import ble_device
from lib.log import log

from concurrent.futures import ThreadPoolExecutor

class ble_scanner:
    callback = None
    uuids = None
    queued_gatts = set()
    gatt_executor = ThreadPoolExecutor(10)

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
        if device.address in self.queued_gatts:
            self.callback(device, None)
        else:
            self.queued_gatts.add(device.address)
            self.gatt_executor.submit(self.connect_gatt, device.address)

    def connect_gatt(self, address):
        async def run():
            log.info(f"Connecting to {address}")
            try:
                async with BleakClient(address) as client:
                    if not client.is_connected:
                        return None
                    gatt_services = []
                    for service in client.services:
                        characteristics = []
                        values = []
                        for char in service.characteristics:
                            properties = char.properties.decode()
                            characteristics.append(GattCharacteristic(char.uuid, properties))
                            try:
                                if 'read' in properties:
                                    value = await client.read_gatt_char(char.uuid)
                                    values.append(value)
                                else:
                                    values.append(None)
                            except Exception:
                                values.append(None)

                        gatt_services.append(GattService(service.uuid, characteristics, values))
                    log.debug(f"Successfully connected to {address}")
                    return gatt_services
            except Exception as e:
                log.debug(f"Error connecting to {address}: {e}")
                return None

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(run())

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
    def __init__(self, uuid, characteristics, values):
        self.uuid = uuid
        self.characteristics = characteristics
        self.values = values

    def __str__(self):
        ret = f"{self.uuid}:\n"
        for char, value in zip(self.characteristics, self.values):
            ret += f"  {char}: {value}\n"
        return ret

class GattCharacteristic:
    def __init__(self, uuid, properties):
        self.uuid = uuid
        self.properties = properties

    def __str__(self):
        return f"{self.uuid}: {', '.join(self.properties)}"

