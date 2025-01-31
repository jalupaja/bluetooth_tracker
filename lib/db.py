from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pickle
import time
import threading

from lib.bt_device import bt_device
from lib.ble_device import ble_device
from lib.log import log

export_all_objects = False

class DB:
    def __init__(self, path):
        self.engine = create_engine(
            f"sqlite:///{path}",
            echo=False,
            pool_size=10,
            max_overflow=20,
            connect_args={"check_same_thread": False}
        )
        self.Session = sessionmaker(bind=self.engine)

    def __del__(self):
        self.close()

    def get_tables(self):
        tables = self.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [t[0] for t in tables]

    def get_columns(self, table):
        columns_info = self.execute(f"PRAGMA table_info({table})")
        return [col[1] for col in columns_info]

    def __execute(self, session, query, *args, retries = 3):
        for _ in range(retries):
            try:
                return session.execute(query, *args)
            except OperationalError as e:
                print("retry")
                if "database is locked" in str(e):
                    time.sleep(0.05)
                else:
                    raise e
        log.info(f"Failed executing {query}")
        return None

    def execute(self, query, *args):
        with self.Session() as session:
            result = self.__execute(session, text(query), *args)
            if result:
                session.commit()
                res = result.fetchall()
                if res:
                    return [tuple(r) for r in res if r]
        return None

    def execute_silent(self, query):
        with self.Session() as session:
            result = self.__execute(session, text(query))
            if result:
                session.commit()

    def execute_rowid(self, query, *args):
        with self.Session() as session:
            result = self.__execute(session, text(query), *args)
            if result:
                session.commit()
                return result.lastrowid
        return None

    def execute_single(self, query, *args):
        with self.Session() as session:
            result = self.__execute(session, text(query), *args)
            if result:
                session.commit()
                res = result.fetchone()
                if res:
                    return tuple(res)
        return None

    def close(self):
        if self.engine:
            self.engine.dispose()
            self.engine = None

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

table_ble_service = """CREATE TABLE IF NOT EXISTS ble_service (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        uuid TEXT,
                        description TEXT,
                        handle INTEGER
                        );"""

table_ble_characteristic = """CREATE TABLE IF NOT EXISTS ble_characteristic (
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
                        handle INTEGER
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

table_ble_char_desc = """CREATE TABLE IF NOT EXISTS ble_char_desc (
                      device_id INTEGER,
                      device_address TEXT,
                      service_id INTEGER,
                      char_id INTEGER,
                      desc_id INTEGER,
                      FOREIGN KEY (device_id) REFERENCES ble_device (id),
                      FOREIGN KEY (service_id) REFERENCES ble_service (id),
                      FOREIGN KEY (char_id) REFERENCES ble_characteristic (id),
                      FOREIGN KEY (desc_id) REFERENCES ble_descriptor (id),
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
            self.db.execute_silent(table_time)
            self.db.execute_silent(table_bluetooth_device_time)
            self.db.execute_silent(table_bluetooth_device)
            self.db.execute_silent(table_bluetooth_service)
            self.db.execute_silent(table_bluetooth_device_service)

            log.debug("bluetooth tables created successfully.")
        except Exception as e:
            log.error(f"Error creating Bluetooth tables: {e}")

    def create_ble_tables(self):
        try:
            self.db.execute_silent(table_time)
            self.db.execute_silent(table_ble_device_time)
            self.db.execute_silent(table_ble_device)
            self.db.execute_silent(table_ble_service)
            self.db.execute_silent(table_ble_characteristic)
            self.db.execute_silent(table_ble_descriptor)
            self.db.execute_silent(table_ble_device_char)
            self.db.execute_silent(table_ble_char_desc)

            log.debug("ble tables created successfully.")
        except Exception as e:
            log.error(f"Error creating BLE tables: {e}")

    def __create_where_clause__(self, columns: dict):
        clauses = []
        params = {}

        for col, val in columns.items():
            if val is None:
                clauses.append(f"{col} IS NULL")
            else:
                clauses.append(f"{col} = :{col}")
                params[col] = val

        return " AND ".join(clauses), params

    def __select_exactly__(self, table, columns: dict):
        try:
            where_clause, params = self.__create_where_clause__(columns)
            return self.db.execute_single(f"SELECT * FROM {table} WHERE {where_clause}", params)
        except Exception as e:
            log.warning(f"Error fetching items from {table}: {e}")

        return None

    def __insert_unique__(self, table, columns: dict):
        try:
            data = self.__select_exactly__(table, columns)
            if (data is None or len(data) <= 0):
                return self.db.execute_rowid(f"""INSERT OR IGNORE INTO {table} ({", ".join([col for col in columns.keys()])})
                               VALUES ({", ".join([f":{c}" for c in columns.keys()])});""",
                               columns)
            else:
                return data[0]

        except Exception as e:
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
                                    }

                                desc_id = self.__insert_unique__("ble_descriptor", gatt_desc)

                                device_desc = {
                                        "device_id": device_id,
                                        "device_address": device.address,
                                        "service_id": svc_id,
                                        "char_id": char_id,
                                        "desc_id": desc_id,
                                        }

                                self.__insert_unique__("ble_char_desc", device_desc)


    def close(self):
        self.db.close()

