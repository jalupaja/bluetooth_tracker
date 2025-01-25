from bleak import BleakScanner, BleakError, BleakClient
import threading
import time
import asyncio
from queue import Queue

from lib.ble_device import ble_device
from lib.log import log

class ble_scanner:
    callback = None
    uuids = None
    queued_gatts = set()

    def __init__(self, callback):
        self.callback = callback
        self.loop = None
        self.gatt_queue = Queue()

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
            self.gatt_queue.put(device)

    async def _scan_gatt(self):
        try:
            while True:
                device = await asyncio.to_thread(self.gatt_queue.get)
                gatt_services = await self.connect_gatt(device.address)
                self.callback(device, gatt_services)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            log.error("Failed getting BLE infos")

    async def connect_gatt(self, address):
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

                return gatt_services
        except Exception as e:
            return None

    def scan(self):
        def run_gatt_loop():
            self.gatt_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.gatt_loop)

            try:
                self.gatt_loop.run_until_complete(self._scan_gatt())
            except Exception as e:
                log.error(f"Error in gatt loop: {e}")
            finally:
                self.gatt_loop.close()

        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            try:
                self.loop.run_until_complete(self._scan())
            except Exception as e:
                log.error(f"Error in scanning loop: {e}")
            finally:
                self.loop.close()

        t1 = threading.Thread(target=run_loop, daemon=True)
        t2 = threading.Thread(target=run_gatt_loop, daemon=True)
        t1.start()
        t2.start()

    def stop(self):
        if self.loop:
            asyncio.run_coroutine_threadsafe(self._shutdown_loop(self.loop), self.loop)
        if self.gatt_loop:
            asyncio.run_coroutine_threadsafe(self._shutdown_loop(self.gatt_loop), self.gatt_loop)

    async def _shutdown_loop(self, loop):
        for task in asyncio.all_tasks(loop):
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

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

