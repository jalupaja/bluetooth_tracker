import sqlite3
import numpy as np
import pandas as pd
import datetime
from collections import Counter
from tabulate import tabulate

DB_PATH = "db.db"

class DB:
    def __init__(self, path):
        self.con = sqlite3.connect(path)
        self.cur = self.con.cursor()

    def get_tables(self):
        tables = self.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [t[0] for t in tables]

    def get_columns(self, table):
        columns_info = self.execute(f"PRAGMA table_info({table})")
        return [col[1] for col in columns_info]

    def execute(self, query):
        self.cur.execute(query)
        return self.cur.fetchall()

db = DB(DB_PATH)

class BLE_device:
    def __init__(self, struct):
        self.id = struct[0]
        self.name = struct[1]
        self.name2 = struct[2]
        self.address = struct[3]
        self.address2 = struct[4]
        self.addresstype = struct[5]
        self.alias = struct[6]
        self.appearance = struct[7]
        self.paired = struct[8]
        self.bonded = struct[9]
        self.trusted = struct[10]
        self.blocked = struct[11]
        self.legacypairing = struct[12]
        self.connected = struct[13]
        self.uuids = struct[14]
        self.manufacturers = struct[15]
        self.manufacturer_binary = struct[16]
        self.servicedata = struct[17]
        self.txpower = struct[18]
        self.advertisingflags = struct[19]
        self.servicesresolved = struct[20]
        self.class_name = struct[21]
        self.modalias = struct[22]
        self.icon = struct[23]

# TABLES:
class BLE_stats:
    TBL_TIME = "time"
    TBL_DEV = "ble_device"
    TBL_DEV_TIME = "ble_device_time"

    def __init__(self):
        self.db = DB(DB_PATH)
        # TODO check if loading everything is too much...
        col_names = self.db.get_columns(self.TBL_DEV)

        boring_cols = [
            "path",
            "alias",
            "paired",
            "bonded",
            "trusted",
            "blocked",
            "legacypairing",
            "rssi",
            "connected",
            "adapter",
            # "manufacturer_binary",
            "txpower",
            "servicesresolved", # TODO
            "class_name", # TODO
            "modalias", # TODO
            "geolocation",
            "AdvertisingFlags", # TODO
        ]

        arr = np.array(self.db.execute(f"SELECT * FROM {dev}"))
        df = pd.DataFrame(arr, columns = col_names)

        # remove uninteresting columns
        df = df.drop(boring_cols, axis = 1)
        # fix timestamp datatype
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        self.df = df

    def get_address(self, add):
        return self.df[self.df["address"] == add]

    def get_manufacturer(self, add):
        return self.df[self.df["manufacturers"] == add]

    def count_table(self, col):
        return self.df.groupby(col)[col].count().sort_values(ascending = False)

    def __interesting_queries():
        df = self.df

        # all columns where name != name2
        df[df['name2'].notna() & (df['name'] != df['name2'])][["name", "name2", "address", "addresstype"]]

        # get all columns where address != address2
        df[df['address2'].notna() & (df['address'] != df['address2'])][["address", "address2"]]

        # get all manufacturer_binary that could not resolve to a manufacturer
        df[(df['manufacturers'].isna() & df['manufacturer_binary'].notna())][["manufacturers", "manufacturer_binary", "address"]]

        # get all manufacturers
        df['manufacturers'].unique()

        # Group by 'address' and get the first and last timestamp for each group
        grouped = df.groupby('address')['timestamp'].agg(['first', 'last'])
        # Calculate the difference in minutes
        grouped['minutes_diff'] = (grouped['last'] - grouped['first']).dt.total_seconds() / 60

class BT_service:
    def __init__(self, struct):
        self.id = struct[0]
        self.host = struct[1]
        self.name = struct[2]
        self.service_classes = struct[3]
        self.profiles = struct[4]
        self.description = struct[5]
        self.provider = struct[6]
        self.service_id = struct[7]
        self.protocol = struct[8]
        self.port = struct[9]

        self.timings = []

    def __getitem__(self, item):
        # not nice but makes things so much easier
        return eval(f"self.{item}")

    def __eq__(self, other):
        return self.id == other.id

    def get_attributes(self):
        return ["host", "name", "service_classes", "profiles", "description", "provider", "service_id", "protocol", "port"]

    def __str__(self):
        ret_str = ""
        for attr in self.get_attributes():
            ret_str += f"{attr}: {self[attr]}\n"
        return ret_str


class BT_device:
    def __init__(self, struct):
        # input from database
        self.id = struct[0]
        self.address = struct[1]
        self.name = struct[2]
        self.device_class = struct[3]
        self.manufacturer = struct[4]
        self.version = struct[5]
        self.hci_version = struct[6]
        self.lmp_version = struct[7]
        self.device_type = struct[8]
        self.device_id = struct[9]
        self.extra_hci_info = struct[10]
        # TODO remove from scanner?/ add old_services parser
        # self.services = struct[11] # TODO

        self.timings = []
        self.services: [BT_service] = []

    def __getitem__(self, item):
        # not nice but makes things so much easier
        return eval(f"self.{item}")

    def get_attributes(self):
        return ["address", "name", "device_class", "manufacturer", "version", "hci_version", "lmp_version", "device_type", "device_id", "extra_hci_info"]

    def __parse_timings(self, timings):
        ret = []
        for t in timings:
            time = datetime.datetime.strptime(t[0], "%Y-%m-%d %H:%M:%S")
            geo = t[1]
            ret.append((time, geo))

        return ret

    def add_timings(self, timings):
        self.timings = self.__parse_timings(timings)

    def add_services(self, services, svc_timings):
        for svc, timing in zip(services, svc_timings):
            service = BT_service(svc)
            service.timings = self.__parse_timings(timing)

            self.services.append(service)

    def get_timings_minmax(self):
        if len(self.timings) <= 0:
            return None
        timings = [t[0] for t in self.timings]
        cur_min = timings[0]
        cur_max = timings[0]
        for t in timings[1:]:
            if t < cur_min:
                cur_min = t
            elif t > cur_max:
                cur_max = t
        return cur_min, cur_max

    def __str__(self):
        ret_str = ""
        for attr in self.get_attributes():
            ret_str += f"{attr}: {self[attr]}\n"
        return ret_str


class BT_stats:
    TBL_TIME = "time"
    TBL_DEV = "bluetooth_device"
    TBL_SVC = "bluetooth_service"
    TBL_DEV_SVC = "bluetooth_device_service"
    TBL_DEV_TIME = "bluetooth_device_time"

    interest_score = -1
    summary = None

    none_values = [
            None,
            """
Requesting information ...""",
            ]

    def __init__(self, device_id = None):
        self.db = DB(DB_PATH)
        if device_id is not None:
            self.parse_id(device_id)

        self.TBL_DEV_names = self.db.get_columns(self.TBL_DEV)
        self.TBL_SVC_names = self.db.get_columns(self.TBL_SVC)

    def search_device(self, search):
        return pd.Series(self.db.execute(f"SELECT id, name, address FROM {self.TBL_DEV} WHERE name LIKE '%{search}%'")).unique()

    def parse_id(self, device_id):
        self.dev_origin = self.__get_id(device_id)
        interest_score = 0
        summary = ""

        for attribute in ["address", "name"]: # TODO name, ...
            summary += f"\n\n--- PARSING {attribute.upper()} {self.dev_origin[attribute]} ---\n"
            devices = self.get_devices_by_attribute(attribute, dev_origin = self.dev_origin)
            i_score, r_str  = self.__devices_comparison(devices)
            interest_score += i_score
            summary += r_str

        self.interest_score = interest_score
        self.summary = summary

    def __get_id(self, device_id):

        dev = BT_device(
                self.db.execute(f"SELECT * FROM {self.TBL_DEV} WHERE id = '{device_id}'")[0]
                )

        dev.add_timings(self.db.execute(f"""SELECT t.timestamp, t.geolocation FROM {self.TBL_TIME} t
                            INNER JOIN {self.TBL_DEV_TIME} dt ON t.id = dt.time_id
                            WHERE dt.device_id = {device_id}
                            """))

        services = self.db.execute(f"""SELECT * FROM {self.TBL_SVC} s
                                       INNER JOIN {self.TBL_DEV_SVC} ds ON s.id = ds.service_id
                                       WHERE ds.device_id = {device_id}
                                       """)

        svc_timings = []
        for svc in services:
            svc_timings.append(self.db.execute(f"""SELECT t.timestamp, t.geolocation FROM {self.TBL_TIME} t
                                INNER JOIN {self.TBL_DEV_SVC} ds ON t.id = ds.time_id
                                WHERE ds.service_id = {svc[0]}
                                """))
        dev.add_services(services, svc_timings)

        return dev

    def get_devices_by_attribute(self, attribute, val = None, dev_origin: BT_device = None):
        if val:
            origin_id = -1 # ignore
            devices = []
        elif dev_origin:
            val = dev_origin[attribute]
            origin_id = dev_origin.id
            devices = [dev_origin]
        else:
            return None

        dev_ids = self.db.execute(
                    f"SELECT id FROM {self.TBL_DEV} WHERE {attribute} = '{val}' AND id != {origin_id}"
                    )
        dev_ids = [i[0] for i in dev_ids]

        for dev_id in dev_ids:
            devices.append(self.__get_id(dev_id))

        return devices

    def __devices_comparison(self, devices: [BT_device]):
        interest_score = 0
        ret_str = ""

        minmax = [dev.get_timings_minmax() for dev in devices]
        overall_min = min([mx[0] for mx in minmax])
        overall_max = max([mx[1] for mx in minmax])

        ret_str += f"Found device {len(devices)} time{'s' if len(devices) == 1 else ''} with an overall range of {overall_max - overall_min}:\n"

        # TODO maybe sort them by min timing
        for dev in devices:
            d_min, d_max = dev.get_timings_minmax()
            if len(dev.timings) == 1:
                ret_str += f"\ton {d_max}\n"
            else:
                ret_str += f"\ton {d_min} - {d_max} ({len(dev.timings)} times in a span of {d_max - d_min})\n"

        def __devices_attribute(devices, val):
            return [dev[val] for dev in devices]

        def __unique(arr):
            # TODO tables also bluetooth specific
            arr = [a for a in arr if a not in self.none_values] # TODO Bluetooth specific
            return pd.Series(arr).unique()

        if len(devices) > 1:
            ret_str += "COMPARING OCCURRENCES:\n"

            for attr in devices[0].get_attributes():
                info = __devices_attribute(devices, attr)
                u_info = __unique(info)

                if len(u_info) <= 1:
                    continue

                interest_score += 1

                ret_str += f"{attr}: {len(u_info)} unique occurrences\n"
                for k, v in Counter(info).items():
                    ret_str += f"\t{v} * \"{k}\"\n"
            else:
                ret_str += "There are no changed types other then false reads"


        # TODO services
        # # for svc in self.services:
        #     if len(svc) <= 0:
        #         continue
        #     pass
            # TODO print services + changes

        return interest_score, ret_str


def arr_sel(arr: np.ndarray, names: list, sel_names: list):
    indexes = [names.index(s) for s in sel_names]
    return arr[indexes]


# TODO TESTING
bt = BT_stats()
# ble = BLE_stats()

print(bt.search_device("HUAWEI P30 Pro"))
bt.parse_id(50)

print(bt.interest_score)
print(bt.summary)
# bt.set_addr(addr)
# TODO use existing device.py files?

# print(bt)


