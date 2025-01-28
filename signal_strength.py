import asyncio
import threading
import time
from datetime import datetime
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from lib.log import log
from lib.ble_device import ble_device
from lib.ble_scanner import ble_scanner
from lib.UI import TUITable, GUIGraph

def addr_callback(device: BLEDevice, advertisement_data: AdvertisementData):
    if device.address != search_address:
        return

    tx_power = advertisement_data.tx_power
    rssi = advertisement_data.rssi
    if not tx_power and not rssi:
        return

    graph.update(tx_power, rssi)
    return

    print(f"{tx_power}\t{rssi}", end = '')
    try:
        if tx_power and rssi:
            print(f"\t{abs(tx_power) - abs(rssi)}", end='') # TODO wrong
    except ValueError:
        pass
    print("")

def tui_callback(device: BLEDevice, advertisement_data: AdvertisementData):
    dev = ble_device(device)
    dev.parse_manufacturer()
    devs.append(dev)
    table.update(dev)

devs = []

# get all devices with low RSSI (and there timeline)
import numpy as np
def get_timings(devs):
    # devs = [d for d in devs if d.rssi > -60]
    timestamps = [datetime.strptime(d.timestamp, '%Y-%m-%d %H:%M:%S') for d in devs]
    diffs = np.array([(timestamps[i+1] - timestamps[i]).total_seconds() for i in range(len(timestamps) - 1)])
    print(f"{diffs.size} discoveries have an avg of {diffs.mean()}")
    return diffs

# {d.name for d in dev_m}

def print_options(data):
    ind_width = len(str(len(data)))
    name_width = max(len(d['name']) for d in data)
    type_width = max(len(d['device_type']) for d in data)
    manu_width = max(len(d['manufacturer']) for d in data)

    row_format = f"{{:<{ind_width}}}  {{:<{name_width}}}  {{:<{type_width}}}  {{:<{manu_width}}}"

    for i, option in enumerate(data):
        print(row_format.format(
            i + 1,
            option['name'],
            option['device_type'],
            option['manufacturer']
        ))

if __name__ == "__main__":
    search_address = None
    table = TUITable()

    address_scaner = ble_scanner(tui_callback)

    address_scaner.scan()
    table.run()
    address_scaner.stop()

    options = table.get_sorted_data()
    if options:
        while True:
            print_options(options)

            choice = input("index: ")
            try:
                choice = int(choice)
            except ValueError:
                continue
            search_address = options[choice - 1]['address']
            break

    if search_address:
        graph = GUIGraph()

        addr_scanner = ble_scanner(addr_callback)
        addr_scanner.scan()

        graph.run()

        addr_scanner.stop()
