import asyncio
from bleak import BleakScanner

from ble_parser import BLE_Parser
from db import DB

db = DB()

devices = None
async def main():
    devices = await BleakScanner.discover()
    parsed_devices = []

    for d in devices:
        dev = BLE_Parser(d)
        print(f"found device: {dev.name} ({dev.address})")
        parsed_devices.append(dev)

        db.insert_device(dev)

    return parsed_devices

if __name__ == "__main__":

    devices = asyncio.run(main())

    # for d in devices:
    #     d.print()
