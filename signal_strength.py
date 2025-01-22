import asyncio
import threading
import time
from datetime import datetime
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

import log
import ble_device
from TUI import TUITable, GUIGraph

# TODO maybe rewrite original?
class BleScanner:
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
    devs.append(ble_device.BleDevice(device))
    table.update(ble_device.BleDevice(device))

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

    ble_scanner = BleScanner(tui_callback)

    ble_scanner.scan()
    table.run()
    ble_scanner.stop()

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

        addr_scanner = BleScanner(addr_callback)
        addr_scanner.scan()

        graph.run()

        addr_scanner.stop()
