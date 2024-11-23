import sqlite3
import pickle
import time
import threading

from bluetooth_device import BluetoothDevice
from ble_device import BleDevice
import log

export_all_objects = True

class BluetoothDatabase:
    def __init__(self, file_path="db.db"):
        self.file_path = file_path
        self.connection = None

    table_time = """CREATE TABLE IF NOT EXISTS time (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP,
                geolocation TEXT
                );"""

    table_bluetooth_device_time = """CREATE TABLE IF NOT EXISTS bluetooth_device_time (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            device_id INTEGER,
                            time_id INTEGER,
                            FOREIGN KEY (device_id) REFERENCES bluetooth_device (id),
                            FOREIGN KEY (time_id) REFERENCES time (id)
                            );"""

    table_ble_device_time = """CREATE TABLE IF NOT EXISTS ble_device_time (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            device_id INTEGER,
                            time_id INTEGER,
                            FOREIGN KEY (device_id) REFERENCES ble_device (id),
                            FOREIGN KEY (time_id) REFERENCES time (id)
                            );"""

    table_bluetooth_device = """CREATE TABLE IF NOT EXISTS bluetooth_device (
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
                             extra_hci_info TEXT,
                             services TEXT
                             );"""

    table_ble_device = """CREATE TABLE IF NOT EXISTS ble_device (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        name2 TEXT,
                        address TEXT,
                        address2 TEXT,
                        addresstype TEXT,
                        alias TEXT,
                        appearance TEXT,
                        paired BOOLEAN,
                        bonded BOOLEAN,
                        trusted BOOLEAN,
                        blocked BOOLEAN,
                        legacypairing BOOLEAN,
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
                        icon TEXT
                        ) """

    table_bluetooth_service = """CREATE TABLE IF NOT EXISTS bluetooth_service (
                              id INTEGER PRIMARY KEY AUTOINCREMENT,
                              host TEXT,
                              name TEXT,
                              service_classes TEXT,
                              profiles TEXT,
                              description TEXT,
                              provider TEXT,
                              service_id TEXT,
                              protocol TEXT,
                              port INTEGER
                              );"""

    table_bluetooth_device_service = """CREATE TABLE IF NOT EXISTS bluetooth_device_service (
                                     device_id INTEGER,
                                     service_id INTEGER,
                                     time_id INTEGER,
                                     FOREIGN KEY (device_id) REFERENCES bluetooth_device (id),
                                     FOREIGN KEY (service_id) REFERENCES bluetooth_service (id),
                                     FOREIGN KEY (time_id) REFERENCES time (id)
                                     );"""

    def connect(self):
        try:
            self.connection = sqlite3.connect(self.file_path)
            log.debug(f"Connection established to {self.file_path}")
        except sqlite3.Error as e:
            log.debug(f"Error creating database connection: {e}")
            self.connection = None

    def create_bluetooth_tables(self):
        try:
            if self.connection:
                cursor = self.connection.cursor()

                cursor.execute(self.table_time)
                cursor.execute(self.table_bluetooth_device_time)
                cursor.execute(self.table_bluetooth_device)
                cursor.execute(self.table_bluetooth_service)
                cursor.execute(self.table_bluetooth_device_service)

                self.connection.commit()
                log.debug("bluetooth tables created successfully.")
        except sqlite3.Error as e:
            log.error(f"Error creating Bluetooth tables: {e}")

    def create_ble_table(self):
        try:
            if self.connection:
                cursor = self.connection.cursor()

                cursor.execute(self.table_time)
                cursor.execute(self.table_ble_device_time)
                cursor.execute(self.table_ble_device)

                self.connection.commit()
                log.debug("ble tables created successfully.")
        except sqlite3.Error as e:
            log.error(f"Error creating BLE tables: {e}")

    def init(self):
        self.connect()
        self.create_bluetooth_tables()
        self.create_ble_table()

    def __create_where_clause__(self, columns: dict):
        clauses = []
        params = []

        for col, val in columns.items():
            if val is None:
                clauses.append(f"{col} IS NULL")
            else:
                clauses.append(f"{col} = ?")
                params.append(val)

        return " AND ".join(clauses), params

    def __select_exactly__(self, table, columns: dict):
        try:
            if self.connection:
                cursor = self.connection.cursor()
                where_clause, params = self.__create_where_clause__(columns)
                cursor.execute(f"SELECT * FROM {table} WHERE {where_clause}", params)
                return cursor.fetchone()
        except sqlite3.Error as e:
            log.warning(f"Error fetching items from {table}: {e}")

        return None

    def __insert_unique__(self, table, columns: dict):
        try:
            if self.connection:
                data = self.__select_exactly__(table, columns)
                if (data is None or len(data) <= 0):
                    cursor = self.connection.cursor()
                    cursor.execute(f"""INSERT OR IGNORE INTO {table} ({", ".join([col for col in columns.keys()])})
                                   VALUES ({", ".join(['?'] * len(columns))});""",
                                   list(columns.values()))
                    self.connection.commit()
                    return cursor.lastrowid
                else:
                    return data[0]

        except sqlite3.Error as e:
            log.warning(f"Error inserting {table} into database: {e}")

        return None

    def insert_bluetooth_device(self, device: BluetoothDevice):
        time_data = {"timestamp": device.timestamp,
                     "geolocation": device.geolocation,
                     }

        time_id = self.__insert_unique__("time", time_data)

        device_data = {
                'address': device.address,
                'name': device.name,
                'device_class': device.device_class,
                'manufacturer': device.manufacturer,
                'version': device.version,
                'hci_version': device.hci_version,
                'lmp_version': device.lmp_version,
                'device_type': device.device_type,
                'device_id': device.device_id,
                # 'rssi': device.rssi,
                'extra_hci_info': device.extra_hci_info,
                }

        device_id = self.__insert_unique__("bluetooth_device", device_data)

        device_time_data = {
                "device_id": device_id,
                "time_id": time_id,
                }

        self.__insert_unique__("bluetooth_device_time", device_time_data)

        for service in device.services:
            # flatten lists in service
            service_data = {k: ", ".join(map(str, v)) if isinstance(v, list) else v for k, v in service.items()}

            service_id = self.__insert_unique__("bluetooth_service", service_data)

            device_service_data = {
                    "device_id": device_id,
                    "service_id": service_id,
                    "time_id": time_id,
                    }

            self.__insert_unique__("bluetooth_device_service", device_service_data)
        log.debug(f"Device {device.name} ({device.address}) inserted into the database.")

    def insert_ble_device(self, device: BleDevice):
        time_data = {"timestamp": device.timestamp,
                     "geolocation": device.geolocation,
                     }

        time_id = self.__insert_unique__("time", time_data)

        device_data = {
                'name': device.name,
                'name2': device.name2,
                'address': device.address,
                'address2': device.address2,
                'addresstype': device.addresstype,
                'alias': device.alias,
                'appearance': device.appearance,
                'paired': device.paired,
                'bonded': device.bonded,
                'trusted': device.trusted,
                'blocked': device.blocked,
                'legacypairing': device.legacypairing,
                # 'rssi': device.rssi,
                'connected': device.connected,
                'uuids': device.uuids,
                'manufacturers': device.manufacturers,
                'manufacturer_binary': device.manufacturer_binary,
                'ServiceData': device.servicedata,
                'AdvertisingFlags': device.advertisingflags,
                'txpower': device.txpower,
                'servicesresolved': device.servicesresolved,
                'class_name': device.class_name,
                'modalias': device.modalias,
                'icon': device.icon,
                }

        device_id = self.__insert_unique__("ble_device", device_data)

        device_time_data = {
                "device_id": device_id,
                "time_id": time_id,
                }

        self.__insert_unique__("ble_device_time", device_time_data)

        log.debug(f"BLE Device {device.name} ({device.address}) inserted into the database.")

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
        if export_all_objects:
            self.export_object(bluetooth_device, f"export/bluetooth/{bluetooth_device.timestamp}-{bluetooth_device.address}")
        self.bluetooth_devices.append(bluetooth_device)

    def add_ble_devices(self, ble_device: BleDevice):
        if export_all_objects:
            self.export_object(ble_device, f"export/ble/{ble_device.timestamp}-{ble_device.address}")
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

