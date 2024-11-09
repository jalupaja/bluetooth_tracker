import sqlite3
import pickle
import time
import threading

from bluetooth_device import BluetoothDevice
from ble_device import BleDevice
import log

class BluetoothDatabase:
    def __init__(self, file_path="db.db"):
        self.file_path = file_path
        self.connection = None

    def connect(self):
        try:
            self.connection = sqlite3.connect(self.file_path)
            log.debug(f"Connection established to {self.file_path}")
        except sqlite3.Error as e:
            log.debug(f"Error creating database connection: {e}")
            self.connection = None

    def create_bluetooth_table(self):
        try:
            if self.connection:
                cursor = self.connection.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS bluetooth_devices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        address TEXT,
                        name TEXT,
                        device_class TEXT,
                        manufacturer TEXT,
                        version TEXT,
                        hci_version TEXT,
                        lmp_version TEXT,
                        device_type TEXT,
                        device_id TEXT,
                        rssi INTEGER,
                        extra_hci_info TEXT,
                        services TEXT,
                        timestamp TIMESTAMP,
                        geolocation TEXT
                    );
                """)
                self.connection.commit()
                log.debug("Table `bluetooth_devices` created successfully.")
        except sqlite3.Error as e:
            log.error(f"Error Bluetooth creating table: {e}")

    def create_ble_table(self):
        try:
            if self.connection:
                cursor = self.connection.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ble_devices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        name2 TEXT,
                        address TEXT,
                        address2 TEXT,
                        addresstype TEXT,
                        alias TEXT,
                        paired BOOLEAN,
                        bonded BOOLEAN,
                        trusted BOOLEAN,
                        blocked BOOLEAN,
                        legacypairing BOOLEAN,
                        rssi INTEGER,
                        connected BOOLEAN,
                        uuids TEXT,
                        manufacturers TEXT,
                        manufacturer_binary BLOB,
                        ServiceData TEXT,
                        AdvertisingFlags BLOB,
                        txpower INTEGER,
                        servicesresolved BOOLEAN,
                        class_name TEXT,
                        modalias TEXT,
                        icon TEXT,
                        timestamp TIMESTAMP,
                        geolocation TEXT
                    )
                ''')
                self.connection.commit()
                log.debug("Table `ble_devices` created successfully.")
        except sqlite3.Error as e:
            log.error(f"Error BLE creating table: {e}")

    def init(self):
        self.connect()
        self.create_bluetooth_table()
        self.create_ble_table()

    def insert_bluetooth_device(self, device: BluetoothDevice):
        try:
            if self.connection:
                cursor = self.connection.cursor()

                services_json = str(device.services)
                device_data = (
                    device.address,
                    device.name,
                    device.device_class,
                    device.manufacturer,
                    device.version,
                    device.hci_version,
                    device.lmp_version,
                    device.device_type,
                    device.device_id,
                    device.rssi,
                    device.extra_hci_info,
                    services_json,
                    device.timestamp,
                    device.geolocation
                )

                cursor.execute("""
                    INSERT INTO bluetooth_devices (address, name, device_class, manufacturer, version,
                    hci_version, lmp_version, device_type, device_id, rssi, extra_hci_info, services, timestamp,
                    geolocation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, device_data)

                self.connection.commit()
                log.debug(f"Device {device.name} ({device.address}) inserted into the database.")
        except sqlite3.Error as e:
            log.warning(f"Error inserting bluetooth device into database: {e}")

    def insert_ble_device(self, device: BleDevice):
        try:
            if self.connection:
                cursor = self.connection.cursor()

                device_data = (
                        device.name,
                        device.name2,
                        device.address,
                        device.address2,
                        device.addresstype,
                        device.alias,
                        device.paired,
                        device.bonded,
                        device.trusted,
                        device.blocked,
                        device.legacypairing,
                        device.rssi,
                        device.connected,
                        device.uuids,
                        device.manufacturers,
                        device.manufacturer_binary,
                        device.servicedata,
                        device.advertisingflags,
                        device.txpower,
                        device.servicesresolved,
                        device.class_name,
                        device.modalias,
                        device.icon,
                        device.timestamp,
                        device.geolocation,
                    )

                cursor.execute("""
                    INSERT INTO ble_devices (
                        name, name2, address, address2, addresstype, alias,
                        paired, bonded, trusted, blocked, legacypairing, rssi,
                        connected, uuids, manufacturers, manufacturer_binary,
                        ServiceData, AdvertisingFlags, txpower, servicesresolved, class_name,
                        modalias, icon, timestamp, geolocation
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, device_data)
                self.connection.commit()
                log.debug(f"BLE Device {device.name} ({device.address}) inserted into the database.")
        except sqlite3.Error as e:
            log.warning(f"Error inserting BLE device into database: {e}")

    def close(self):
        if self.connection:
            self.connection.close()
            log.debug("Database connection closed.")

class Exporter:
    def __init__(self, db_file_path):
        self.db = BluetoothDatabase(db_file_path)
        self.export = True
        self.bluetooth_devices = []
        self.ble_devices = []

    def add_bluetooth_devices(self, bluetooth_device: BluetoothDevice):
        self.bluetooth_devices.append(bluetooth_device)

    def add_ble_devices(self, ble_device: BleDevice):
        self.ble_devices.append(ble_device)

    def export_object(self, obj, file_name):
        with open(f"{file_name}.pk1", 'wb') as f:
            pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

    def import_object(self, file_name):
        with open(file_name, 'rb') as f:
            return pickle.load(f)

    def export_devices(self):
        self.db.init()

        while self.export:
            while len(self.bluetooth_devices) > 0:
                log.debug("Exporting bluetooth device")
                self.db.insert_bluetooth_device(self.bluetooth_devices.pop())

            while len(self.ble_devices) > 0:
                log.debug("Exporting ble device")
                self.db.insert_ble_device(self.ble_devices.pop())

            time.sleep(1)

        self.db.close()

    def start_exporting(self):
        log.debug("Exporting Thread started")
        scan_thread = threading.Thread(target=self.export_devices)
        scan_thread.daemon = True
        scan_thread.start()

    def stop_exporting(self):
        self.export = False
        log.debug("Exporting Thread stopped")

