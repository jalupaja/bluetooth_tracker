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

    def execute(self, query, *args):
        cur = self.con.cursor()
        if len(args) > 0:
            cur.execute(query, *args)
        else:
            cur.execute(query)
        res = cur.fetchall()
        cur.close()
        return res

    def execute_rowid(self, query, *args):
        cur = self.con.cursor()
        if len(args) > 0:
            cur.execute(query, *args)
        else:
            cur.execute(query)
        self.commit()
        res = cur.lastrowid
        cur.close()
        return res

    def execute_single(self, query, *args):
        cur = self.con.cursor()
        if len(args) > 0:
            cur.execute(query, *args)
        else:
            cur.execute(query)
        res = cur.fetchone()
        cur.close()
        return res

    def commit(self):
        self.con.commit()

    def close(self):
        self.__del__()

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

table_ble_services = """CREATE TABLE IF NOT EXISTS ble_service (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        uuid TEXT,
                        description TEXT,
                        handle INTEGER
                        );"""

table_ble_characteristics = """CREATE TABLE IF NOT EXISTS ble_characteristic (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        uuid TEXT,
                        value TEXT,
                        description TEXT,
                        handle INTEGER,
                        properties TEXT
                        );"""

table_ble_descriptor = """CREATE TABLE IF NOT EXISTS ble_descriptor (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        uuid TEXT,
                        value TEXT,
                        description TEXT,
                        handle INTEGER,
                        char_id INTEGER,
                        FOREIGN KEY (char_id) REFERENCES ble_characteristic (id)
                        );"""

table_ble_device_char = """CREATE TABLE IF NOT EXISTS ble_device_char (
                        device_id INTEGER,
                        device_address TEXT,
                        service_id INTEGER,
                        char_id INTEGER,
                        FOREIGN KEY (device_id) REFERENCES ble_device (id),
                        FOREIGN KEY (service_id) REFERENCES ble_service (id),
                        FOREIGN KEY (char_id) REFERENCES ble_characteristic (id),
                        PRIMARY KEY (device_id, service_id, char_id)
                        );"""

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


class BluetoothDatabase:
    def __init__(self, file_path="db.db"):
        self.db = DB(file_path)
        self.create_bluetooth_tables()
        self.create_ble_tables()

    def create_bluetooth_tables(self):
        try:
            self.db.execute(table_time)
            self.db.execute(table_bluetooth_device_time)
            self.db.execute(table_bluetooth_device)
            self.db.execute(table_bluetooth_service)
            self.db.execute(table_bluetooth_device_service)

            self.db.commit()
            log.debug("bluetooth tables created successfully.")
        except sqlite3.Error as e:
            log.error(f"Error creating Bluetooth tables: {e}")

    def create_ble_tables(self):
        try:
            self.db.execute(table_time)
            self.db.execute(table_ble_device_time)
            self.db.execute(table_ble_device)
            self.db.execute(table_ble_services)
            self.db.execute(table_ble_characteristics)
            self.db.execute(table_ble_descriptor)
            self.db.execute(table_ble_device_char)

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
        # TODO log.info(f"found BLE device: {device.address} {device.name}")
        time_data = {"timestamp": device.timestamp,
                     "geolocation": device.geolocation,
                     }

        time_id = self.__insert_unique__("time", time_data)

        device_data = device.to_dict()
        device_data.pop("rssi")

        device_id = self.__insert_unique__("ble_device", device_data)

        device_time_data = {
                "device_id": device_id,
                "time_id": time_id,
                }

        self.__insert_unique__("ble_device_time", device_time_data)

        log.debug(f"BLE Device {device.name} ({device.address}) inserted into the database.")

    def insert_ble_services(self, device, services, characteristics, descriptors):
        if services and len(services) > 0:
            device_data = device.to_dict()
            device_data.pop("rssi")

            device_id = self.__insert_unique__("ble_device", device_data)

            for svc in services:
                gatt_service = {
                    "uuid": svc.uuid,
                    "description": svc.description,
                    "handle": svc.handle,
                    }
                svc_id = self.__insert_unique__("ble_service", gatt_service)
                for char in characteristics:
                    if char.service_handle == svc.handle:
                        gatt_char = {
                            "uuid": char.uuid,
                            "value": char.value,
                            "description": char.description,
                            "handle": char.handle,
                            "properties": ", ".join(char.properties),
                            }
                        char_id = self.__insert_unique__("ble_characteristic", gatt_char)

                        device_char = {
                                "device_id": device_id,
                                "device_address": device.address,
                                "service_id": svc_id,
                                "char_id": char_id,
                                }
                        self.__insert_unique__("ble_device_char", device_char)

                        for desc in descriptors:
                            if desc.characteristic_handle == char.handle:
                                gatt_desc = {
                                    "uuid": desc.uuid,
                                    "value": desc.value,
                                    "description": desc.description,
                                    "handle": desc.handle,
                                    "char_id": char_id,
                                    }

                                self.__insert_unique__("ble_descriptor", gatt_desc)

    def close(self):
        self.db.close()

