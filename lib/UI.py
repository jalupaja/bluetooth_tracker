from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.panel import Panel
from datetime import datetime
import matplotlib.pyplot as plt
import time

from lib.ble_device import ble_device
from lib.log import log


class TUITable:
    def __init__(self):
        self.console = Console()
        self.devices = {}
        self.table = self._create_table()
        self.running = False

    def _create_table(self):
        table = Table(title="Available Devices", expand=True)
        table.add_column("Name", justify="left", style="green")
        table.add_column("Manufacturer", justify="left", style="yellow")
        table.add_column("Device Type", justify="left", style="magenta")
        table.add_column("Address", justify="left", style="cyan", no_wrap=True)
        table.add_column("RSSI", justify="let", style="yellow")
        table.add_column("Last Seen (s)", justify="right", style="green")
        return table

    def update(self, device: ble_device):
        new_data = {
            'name': device.name,
            'manufacturer': device.manufacturers,
            'device_type': device.device_type,
            'address': device.address,
            'rssi': device.rssi,
            'last_update': datetime.now(),
            'uuids': device.uuids,
        }

        if new_data.get('address') in self.devices:
            # check if some values should not be updated
            old_data = self.devices[new_data.get('address')]

            # use old value i new value is empty
            for k, v in new_data.items():
                if not v:
                    new_data[k] = old_data[k]

        for k, v in new_data.items():
            if not v:
                new_data[k] = ""

        self.devices[new_data.get('address')] = new_data

    def get_sorted_data(self):
        now = datetime.now()

        # remove devices older then 1 min
        self.devices = {key: value for key, value in self.devices.items()
             if (now - value['last_update']).total_seconds() < 60}

        def sort_key(entry):
            last_seen = (now - entry['last_update']).total_seconds()
            if last_seen < 10:
                age_group = 0
            elif last_seen < 30:
                age_group = 1
            else:
                age_group = 2
            return (age_group, entry['name'])

        return sorted(self.devices.values(), key=sort_key)

    def _update_table(self):
        self.table = self._create_table()
        new_data = self.get_sorted_data()
        now = datetime.now()

        if new_data:
            for entry in new_data:
                last_seen = (now - entry['last_update']).total_seconds()
                if last_seen < 10:
                    age_color = "green"
                elif last_seen < 30:
                    age_color = "orange3"
                else:
                    age_color = "dark_red"

                self.table.add_row(
                    Text(f"{entry['name']}", style=age_color),
                    Text(f"{entry['manufacturer']}", style=None),
                    Text(f"{entry['device_type']}", style=None),
                    Text(f"{entry['address']}", style=None),
                    Text(f"{entry['rssi']}", style=None),
                    Text(f"{int(last_seen)}", style=age_color),
                )

    def run(self):
        self.running = True

        with Live(self.table, console=self.console, refresh_per_second=1) as live:
            while self.running:
                try:
                    self._update_table()
                    live.update(self.table)
                    time.sleep(1)

                except KeyboardInterrupt:
                    self.running = False

class GUIGraph:
    X_MAX = 20 # TODO
    def __init__(self):
        self.measurements = 0
        self.rssi = []
        self.tx_power = []

        self.fig, self.ax = plt.subplots()
        self.ax.set_ylim(-130, 30) # theoretical max range is -120 - +20
        self.ax.set_xlim(0, self.X_MAX)

        self.rssi_line, = self.ax.plot([], [], label="RSSI", color='b')
        self.tx_power_line, = self.ax.plot([], [], label="TX Power", color='g')

        self.ax.set_xlabel("Measurements")
        self.ax.set_ylabel("Values")
        self.ax.legend()

    def update(self, tx_power, rssi):
        if not rssi:
            return
        self.rssi.append(rssi)
        self.tx_power.append(tx_power)
        self.measurements += 1

        if len(self.rssi) > self.X_MAX:
            self.rssi = self.rssi[1:]
            self.tx_power = self.tx_power[1:]

    def render(self):
        x_end = min(self.measurements, self.X_MAX)
        x_start = 0

        x_arr = list(range(x_start, x_end))
        self.rssi_line.set_data(x_arr, self.rssi)
        self.tx_power_line.set_data(x_arr, self.tx_power)

        # update x-labels
        self.ax.set_xticks(range(x_start, x_end + 1, 10))

        x_end = self.measurements
        x_start = max(0, x_end - self.X_MAX)

        self.ax.set_xticklabels([str(i) for i in range(x_start, x_end + 1, 10)])

        self.ax.relim()
        self.ax.autoscale_view(True, True, True)

        if len(self.rssi) > self.X_MAX:
            self.ax.set_xlim(x_start, x_end)

        plt.draw()

    def run(self):
        plt.ion()

        try:
            while True:
                self.render()
                plt.pause(0.5)
        except KeyboardInterrupt:
            # Handle Ctrl+C
            log.debug("\nGraph interrupted by user.")
            self.close()

    def close(self):
        plt.close()

