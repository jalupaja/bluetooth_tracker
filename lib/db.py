import sqlite3
import pickle
import time
import threading

from lib.bt_device import bt_device
from lib.ble_device import ble_device
from lib.log import log

export_all_objects = False

class DB:
    def __init__(self, path):
        self.path = path
        self.con = sqlite3.connect(path, check_same_thread=False)
        self.cur = None

    def __del__(self):
        if self.con:
            self.con.commit()
            self.con.close()
            self.con = None

    def get_tables(self):
        tables = self.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [t[0] for t in tables]

    def get_columns(self, table):
        columns_info = self.execute(f"PRAGMA table_info({table})")
        return [col[1] for col in columns_info]

    def _update_cursor(self):
        if self.cur:
            self.cur.close()
        self.cur = self.con.cursor()

    def execute(self, query, *args):
        self._update_cursor()
        if len(args) > 0:
            self.cur.execute(query, *args)
        else:
            self.cur.execute(query)
        return self.cur.fetchall()

    def execute_rowid(self, query, *args):
        self._update_cursor()
        if len(args) > 0:
            self.cur.execute(query, *args)
        else:
            self.cur.execute(query)
        self.commit()
        return self.cur.lastrowid

    def execute_single(self, query, *args):
        self._update_cursor()
        if len(args) > 0:
            self.cur.execute(query, *args)
        else:
            self.cur.execute(query)
        return self.cur.fetchone()

    def commit(self):
        self.con.commit()

    def close(self):
        self.__del__()

class BluetoothDatabase:
    def __init__(self, file_path="db.db"):
        self.db = DB(file_path)
        self.create_bluetooth_tables()
        self.create_ble_tables()

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
                        AdvertisingData BLOB,
                        txpower INTEGER,
                        servicesresolved BOOLEAN,
                        class_of_device BLOB,
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

    def create_bluetooth_tables(self):
        try:
            self.db.execute(self.table_time)
            self.db.execute(self.table_bluetooth_device_time)
            self.db.execute(self.table_bluetooth_device)
            self.db.execute(self.table_bluetooth_service)
            self.db.execute(self.table_bluetooth_device_service)

            self.db.commit()
            log.debug("bluetooth tables created successfully.")
        except sqlite3.Error as e:
            log.error(f"Error creating Bluetooth tables: {e}")

    def create_ble_tables(self):
        try:
            self.db.execute(self.table_time)
            self.db.execute(self.table_ble_device_time)
            self.db.execute(self.table_ble_device)

            self.db.commit()
            log.debug("ble tables created successfully.")
        except sqlite3.Error as e:
            log.error(f"Error creating BLE tables: {e}")

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
            where_clause, params = self.__create_where_clause__(columns)
            return self.db.execute_single(f"SELECT * FROM {table} WHERE {where_clause}", params)
        except sqlite3.Error as e:
            log.warning(f"Error fetching items from {table}: {e}")

        return None

    def __insert_unique__(self, table, columns: dict):
        try:
            data = self.__select_exactly__(table, columns)
            if (data is None or len(data) <= 0):
                return self.db.execute_rowid(f"""INSERT OR IGNORE INTO {table} ({", ".join([col for col in columns.keys()])})
                               VALUES ({", ".join(['?'] * len(columns))});""",
                               list(columns.values()))
            else:
                return data[0]

        except sqlite3.Error as e:
            log.warning(f"Error inserting {table} into database: {e}")

        return None

    def insert_bluetooth_device(self, device: bt_device):
        log.info(f"found Bluetooth device: {device.address} {device.name}")
        time_data = {"timestamp": device.timestamp,
                     "geolocation": device.geolocation,
                     }

        time_id = self.__insert_unique__("time", time_data)

        device_id = self.__insert_unique__("bluetooth_device", device.to_dict())

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

    def insert_ble_device(self, device: ble_device):
        log.info(f"found BLE device: {device.address} {device.name}")
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
                'AdvertisingData': device.advertisingdata,
                'txpower': device.txpower,
                'servicesresolved': device.servicesresolved,
                'class_of_device': device.class_of_device,
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
        self.db.close()

