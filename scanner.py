import asyncio
from bleak import BleakScanner
from bleak import BleakClient

from ble_parser import BLE_Parser
from db import DB

db = DB()

devices = None

async def main():
    devices = await BleakScanner.discover()
    parsed_devices = []

    # TODO test (nice error msg) if bluetooth is disabled
    for d in devices:
        # TODO test with different devices (has to be a GATT server?)
        client = BleakClient(d)
        # client.connect()
        dev = BLE_Parser(d)
        print(f"found device: {dev.name} ({dev.address}, {dev.manufacturers})")

        # parsed_devices.append(dev)
        parsed_devices.append(client)

        db.insert_device(dev)

    return parsed_devices

if __name__ == "__main__":

    devices = asyncio.run(main())

    # for d in devices:
    #     d.print()
