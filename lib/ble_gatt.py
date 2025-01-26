from bleak import BleakClient
import asyncio
from concurrent.futures import ThreadPoolExecutor

from lib.log import log

class ble_gatt:
    MAX_CONNECTION_TRIES = 3
    finished_gatts = set()
    gatt_tries = {}

    def __init__(self, callback):
        self.gatt_executor = ThreadPoolExecutor(20)
        self.callback = callback

    def add_possible_device(self, device):
        # check if in finished_gatts first
        if not device.address in self.finished_gatts:
            self.add_device(device)

    def add_device(self, device):
        self.finished_gatts.add(device.address)
        self.gatt_executor.submit(self._connect_gatt, device)

    def _connect_gatt(self, device):
        async def _reconnect(client):
            if not client.is_connected:
                await client.connect()

        def _dec_value(value):
            # decode a byte value
            if not value:
                return None
            elif value.isalnum():
                return value.decode('utf-8', errors='replace')
            else:
                return value.hex()

        async def _get_char(client, uuid, try_again = True):
            try:
                if client.is_connected:
                    value = await client.read_gatt_char(uuid)
                    return _dec_value(value)
            except Exception as e:
                await _reconnect(client)
                if try_again: # try again on error
                    return await _get_char(client, uuid, False)
            return None

        async def _get_desc(client, handle, try_again = True):
            try:
                if client.is_connected:
                    value = await client.read_gatt_descriptor(handle)
                    return _dec_value(value)
            except Exception as e:
                await _reconnect(client)
                if try_again: # try again on error
                    return await _get_desc(client, handle, False)
            return None

        async def run(address):
            log.info(f"Connecting to {address}")

            gatt_services = []
            gatt_characteristics = []
            gatt_descriptors = []

            try:
                async with BleakClient(address) as client:
                    if not client.is_connected:
                        log.debug(f"Error connecting to {address}: {e}")
                        return None

                    for svc in client.services.services.values():
                        gatt_services.append(GattService(svc))

                    for char in client.services.characteristics.values():
                        gatt_characteristics.append(GattCharacteristic(char))

                    for desc in client.services.descriptors.values():
                        gatt_descriptors.append(GattDescriptor(desc))

                    generic_access_characteristics = [
                        ("00002a00-0000-1000-8000-00805f9b34fb", "Device Name"),
                        ("00002a01-0000-1000-8000-00805f9b34fb", "Device Appearance"),
                    ]

                    create_generic_access = False
                    for uuid, description in generic_access_characteristics:
                        value = await _get_char(client, uuid)
                        if value:
                            create_generic_access = True

                            char = GattCharacteristic(None)
                            char.description = description
                            char.uuid = uuid
                            char.value = value
                            # char.handle = None # TODO
                            char.service_handle = 0
                            gatt_characteristics.append(char)

                    if create_generic_access:
                        svc = GattService(None)
                        svc.description = "Generic Access"
                        svc.handle = 0
                        svc.uuid = "00001800-0000-1000-8000-00805f9b34fb"
                        gatt_services.append(svc)


                    for char in gatt_characteristics:
                        if 'read' in char.properties:
                            char.value = await _get_char(client, char.uuid)

                    for desc in gatt_descriptors:
                        desc.value = await _get_desc(client, desc.handle)

            except Exception as e:
                log.debug(f"Error connecting to {address}: {e}")

                # TODO maybe not for all errors? maybe it just doesn't have any
                # allow more tries because it failed unexpectedly
                if not address in self.gatt_tries:
                    self.gatt_tries[address] = 0
                self.gatt_tries[address] += 1

                if self.gatt_tries[address] < self.MAX_CONNECTION_TRIES:
                    self.finished_gatts.remove(address) # retry

            self.callback(device, gatt_services, gatt_characteristics, gatt_descriptors)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run(device.address))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            log.error(f"Error in scanning loop: {e}")
        finally:
            self.loop.close()

    def stop(self):
        self.gatt_executor.shutdown(wait=True, cancel_futures=True)

class GattService:
    description = None
    handle = None
    uuid = None
    characteristics = []

    def __init__(self, service):
        if isinstance(service, tuple):
            (_, self.uuid, self.description, self.handle) = service
        elif service:
            self.uuid = service.uuid
            self.description = service.description
            self.handle = service.handle

    def __str__(self):
        ret = f"{self.uuid}: {self.description} ({self.handle})"
        for char in self.characteristics:
            ret += f"\n\t{char}"
        return ret

class GattCharacteristic:
    description = None
    handle = None
    properties = []
    uuid = None
    service_handle = None
    value = None
    descriptors = []

    def __init__(self, char):
        if isinstance(char, tuple):
            (_, self.uuid, self.value, self.description, self.handle, self.properties) = char
            self.properties = self.properties.split(", ")
        elif char:
            self.uuid = char.uuid
            self.description = char.description
            self.handle = char.handle
            self.properties = char.properties
            self.service_handle = char.service_handle

    def __str__(self):
        res = f"{self.uuid}: {self.description} ({self.handle}): {', '.join(self.properties)} = {self.value}"
        for desc in self.descriptors:
            res += f"\n\t- {desc}"

        return res

class GattDescriptor:
    description = None
    handle = None
    uuid = None
    characteristic_handle = None
    value = None

    def __init__(self, desc):
        if isinstance(desc, tuple):
            (_, self.uuid, self.value, self.description, self.handle) = desc
        elif desc:
            self.description = desc.description
            self.handle = desc.handle
            self.uuid = desc.uuid
            self.desc = desc.characteristic_handle

    def __str__(self):
        return f"{self.uuid}: {self.description} ({self.handle}) = {self.value}"

