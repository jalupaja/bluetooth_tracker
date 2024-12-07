import sqlite3
import numpy as np
import pandas as pd
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

# TABLES:
class BLE_stats:
    TBL_TIMe = "time"
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

class BT_stats:
    TBL_TIME = "time"
    TBL_DEV = "bluetooth_device"
    TBL_SVC = "bluetooth_service"
    TBL_DEV_SVC = "bluetooth_device_service"
    TBL_DEV_TIME = "bluetooth_device_time"

    def __init__(self, addr = None):
        self.db = DB(DB_PATH)
        self.addr = addr

        self.TBL_DEV_names = self.db.get_columns(self.TBL_DEV)
        self.TBL_SVC_names = self.db.get_columns(self.TBL_SVC)

        self.__parse_addr()

    def set_addr(self, addr):
        self.addr = addr
        self.__parse_addr()

    def search_device(self, search):
        return pd.Series(self.db.execute(f"SELECT name, address FROM {self.TBL_DEV} WHERE name LIKE '%{search}%'")).unique()


    def __parse_addr(self):
        if self.addr is None:
            return

        self.info = np.array(
                self.db.execute(
                    f"SELECT * FROM {self.TBL_DEV} WHERE address = '{self.addr}'"
                    )
                )
        # dev_ids = [i[0] for i in info]
        #
        # for dev_id in dev_ids:
        #     # TODO
        #     self.db.execute(f"""SELECT t.timestamp FROM time t
        #                         INNER JOIN bluetooth_device_time bdt ON t.id = bdt.time_id
        #                         WHERE bdt.device_id = {dev_id}
        #                     """)
        #
        # # TODO others with same name/...
        # return np.array(info)

    def compare(self, cols = ["id", "name", "address"]):
        df = [arr_sel(i, self.TBL_DEV_names, cols) for i in self.info]

        table = tabulate(df, headers = cols)
        print(table)

def arr_sel(arr: np.ndarray, names: list, sel_names: list):
    indexes = [names.index(s) for s in sel_names]
    return arr[indexes]



# TODO TESTING
bt = BT_stats()
# ble = BLE_stats()

dev = bt.search_device("HUAWEI P30 Pro")
addr = dev[0][1]

bt.set_addr(addr)
# TODO use exising device.py files?
info = bt.info
