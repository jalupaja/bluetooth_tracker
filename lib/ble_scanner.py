from bleak import BleakScanner
import threading
import time
import asyncio

from lib.ble_device import ble_device
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

        while True:
            try:
                await scanner.start()
                await asyncio.sleep(1)
                await scanner.stop()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.info(f"BLE Discovery failed: {e}")
                await asyncio.sleep(1)
                continue

        await scanner.stop()

    def scan(self):
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            try:
                self.loop.run_until_complete(self._scan())
            except asyncio.CancelledError:
                pass
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

        loop.stop()
