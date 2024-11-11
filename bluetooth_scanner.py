import bluetooth
import threading
import time
import subprocess
import log
from concurrent.futures import ThreadPoolExecutor
from bluetooth_device import BluetoothDevice
from db import Exporter

class BluetoothScanner:
    def __init__(self, exporter: Exporter):
        self.exporter = exporter
        self.scanning = True
        self.devices = []
        self.executor = ThreadPoolExecutor(max_workers=10)

    def get_device_info(self, device):
        log.debug(f"Fetching detailed information for Bluetooth device: {device.address}")

        try:
            device_name = bluetooth.lookup_name(device.address, timeout=5)
            if device_name is None:
                device_name = None
        except Exception as e:
            device_name = None
            log.debug(f"Error retrieving Bluetooth device name for {device.address}: {e}")

        device.name = device_name

        try:
            services = bluetooth.find_service(address=device.address)
            if services:
                for service in services:
                    service_info = {
                        'name': service['name'],
                        'description': service['description'],
                        'protocol': service['protocol'],
                        'port': service['port'],
                        'host': service['host'],
                        'service-classes': service['service-classes'],
                        'profiles': service['profiles']
                    }
                    device.add_service(service_info)
            else:
                log.debug("No Bluetooth services found.")
        except Exception as e:
            log.debug(f"Error retrieving services for Bluetooth device {device.address}: {e}")

        # Fetch the device class and other information using `hcitool`
        device_class, manufacturer, version, hci_version, lmp_version, device_type, device_id, extra_info = self.get_device_class_and_info(device.address)
        device.update_device_class(device_class)
        device.set_manufacturer(manufacturer)
        device.set_version(version)
        device.set_hci_version(hci_version)
        device.set_lmp_version(lmp_version)
        device.set_device_type(device_type)
        device.set_device_id(device_id)
        device.set_extra_hci_info(extra_info)

        self.exporter.add_bluetooth_devices(device)

    def get_device_class_and_info(self, address):
        try:
            result = subprocess.run(['hcitool', 'info', address], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout.decode()

            device_class = None
            manufacturer = None
            version = None
            hci_version = None
            lmp_version = None
            device_type = None
            device_id = None
            extra_info = ""

            # Extract relevant information from the hcitool output
            for line in output.splitlines():
                if "Class" in line:
                    device_class = line.split("Class: ")[-1].strip() if "Class" in line else None
                elif "Manufacturer" in line:
                    manufacturer = line.split("Manufacturer: ")[-1].strip() if "Manufacturer" in line else None
                elif "Version" in line:
                    version = line.split("Version: ")[-1].strip() if "Version" in line else None
                elif "HCI Version" in line:
                    hci_version = line.split("HCI Version: ")[-1].strip() if "HCI Version" in line else None
                elif "LMP Version" in line:
                    lmp_version = line.split("LMP Version: ")[-1].strip() if "LMP Version" in line else None
                elif "Device Type" in line:
                    device_type = line.split("Device Type: ")[-1].strip() if "Device Type" in line else None
                elif "Device ID" in line:
                    device_id = line.split("Device ID: ")[-1].strip() if "Device ID" in line else None
                else:
                    extra_info = f"{extra_info}\n{line}"


            return device_class, manufacturer, version, hci_version, lmp_version, device_type, device_id, extra_info

        except Exception as e:
            log.debug(f"Error fetching Bluetooth device info via HCI for {address}: {e}")
            return None, None, None, None, None, None, None, None

    def scan_bluetooth_devices(self):
        while self.scanning:
            log.debug("Scanning for Bluetooth devices...")

            try:
                devices = bluetooth.discover_devices(duration=6, lookup_names=True, flush_cache=True)
            except (bluetooth.BluetoothError, OSError) as e:
                log.debug(f"Bluetooth Discovery failed: {e}")
                time.sleep(1)
                continue

            if devices:
                log.debug(f"Found {len(devices)} Bluetooth device(s):")
                for addr, name in devices:
                    device = BluetoothDevice(address=addr, name=name)
                    self.devices.append(device)
                    log.info(f"Bluetooth Device Address: {addr} | Device Name: {name}")

                    self.executor.submit(self.get_device_info, device)
            else:
                log.debug("No Bluetooth devices found.")

            # TODO
            time.sleep(3)

    def start_scanning(self):
        scan_thread = threading.Thread(target=self.scan_bluetooth_devices)
        scan_thread.daemon = True
        scan_thread.start()

    def stop_scanning(self):
        self.scanning = False
        log.debug("Bluetooth Scanning stopped.")

