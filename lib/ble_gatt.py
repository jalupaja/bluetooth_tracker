from bleak import BleakClient
import asyncio
from concurrent.futures import ThreadPoolExecutor

from lib.log import log

class ble_gatt:
    MAX_CONNECTION_TRIES = 3
    finished_gatts = set()
    gatt_tries = {}

    def __init__(self, callback):
        self.gatt_executor = ThreadPoolExecutor(1)
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

        async def run(address):
            print(address)
            log.info(f"Connecting to {address}")
            print(f"Connecting to {address}")
            try:
                async with BleakClient(address) as client:
                    if not client.is_connected:
                        log.debug(f"Error connecting to {address}: {e}")
                        print(f"Error connecting to {address}: {e}")
                        return None
                    gatt_services = []

                    print("SVC")
                    for svc in client.services.services.values():
                        svc = GattService(svc)
                        svc_characteristics = []
                        svc_descriptors = []
                        for char in svc.characteristics:
                            svc_characteristics.append(GattCharacteristic(char))
                        for desc in svc.descriptors:
                            svc_descriptors.append(GattDescriptor(desc))

                        svc.characteristics = svc_characteristics
                        svc.descriptors = svc_descriptors
                    print()
                    print()
                    print()
                    return None # TODO
                    for handle, char in client.services.characteristics.items():
                        print(f"<- {char.service_handle}")
                        print(f"{char.uuid} ({handle}) {char.description}")

                        if 'read' in char.properties:
                            value = None
                            try:
                                if client.is_connected:
                                    value = await client.read_gatt_char(char.uuid)
                                    value = value.decode()
                            except:
                                await _reconnect(client)

                            print(f"CHAR VAL: {value}")
                        for desc in char.descriptors:
                            print(f"\tdesc: {desc}")
                            value = None
                            try:
                                if client.is_connected:
                                    value = await client.read_gatt_descriptor(char.uuid)
                                    print(f"GOT VAL: {value}")
                                    value = value.decode()
                            except:
                                await _reconnect(client)
                            print(f"\tDESC VAL: {value}")
                    print()
                    print()
                    print()
                    print("DESC")
                    for handle, desc in client.services.descriptors.items():
                        print(f"<- {desc.characteristic_handle}")
                        print(f"{desc.uuid} ({desc.handle}) {desc.description}")
                    print()
                    print()
                    print()
                    return None # TODO

                    for service in client.services:
                        print(service)
                        # TODO need to save name, maybe port
                        characteristics = []
                        print(f"CON1?: {client.is_connected}")
                        # TODO service.descriptors:
                        for desc in service.descriptors:
                            print("DESC")
                        for char in service.characteristics:
                            print(f"char: {char}")
                            saved_char = GattCharacteristic(char)
                            characteristics.append(saved_char)

                            print(f"CON2?: {client.is_connected}")
                            try:
                                print(f"CON3?: {client.is_connected}")
                                if 'read' in char.properties:
                                    # TODO
                                    value = await client.read_gatt_char(char.uuid)
                                    # TODO save
                            except Exception as e:
                                print(f"CON4?: {client.is_connected}")
                                if not client.is_connected:
                                    await client.connect()
                                    # TODO throw error if can't connect?
                                    print(f"recc?: {client.is_connected}")
                                print(f"Failed val: {e}")

                        gatt_services.append(GattService(service, characteristics))
                    log.debug(f"Successfully connected to {address}")
                    print(f"Successfully connected to {address}")
                    return gatt_services
            except Exception as e:
                log.debug(f"Error connecting to {address}: {e}")
                print(f"Error(LATR) connecting to {address}: {e}")

                # TODO maybe not for all errors? maybe it just doesn't have any
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
        print("finished gatt")
        # TODO self.callback(device, services)

    async def _shutdown(self):
        self.gatt_executor.shutdown(wait=True)

class GattService:
    def __init__(self, service):
        self.description = service.description
        self.handle = service.handle
        self.uuid = service.uuid
        self.characteristics = []
        self.descriptors = []

    def parse_descriptors(self):
        # TODO add descriptors to characteristics
        pass

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
        self.service_handle = char.service_handle
        self.value = None

    def __str__(self):
        return f"{self.uuid}: {self.description} ({self.handle}): {', '.join(self.properties)} = {self.value}"

class GattDescriptor:
    def __init__(self, char):
        self.description = char.description
        self.handle = char.handle
        self.uuid = char.uuid
        self.characteristic_handle = char.characteristic_handle
        self.value = None

    def __str__(self):
        return f"{self.uuid}: {self.description} ({self.handle}): {', '.join(self.properties)} = {self.value}"

