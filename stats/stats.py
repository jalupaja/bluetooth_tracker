import numpy as np
import pandas as pd
from collections import Counter
from tabulate import tabulate

from BT_device import BT_device
from db import DB

class BT_stats:
    # TODO bluetooth specific
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

    def __init__(self, db, device_id = None):
        self.db = db
        if device_id is not None:
            self.parse_id(device_id)

        self.TBL_DEV_names = self.db.get_columns(self.TBL_DEV)
        self.TBL_SVC_names = self.db.get_columns(self.TBL_SVC)

    def get_all_devices(self):
        return pd.Series(self.db.execute(f"SELECT id, name, address FROM {self.TBL_DEV}")).unique()

    def search_device(self, search):
        return pd.Series(self.db.execute(f"SELECT id, name, address FROM {self.TBL_DEV} WHERE name LIKE '%{search}%'")).unique()

    def parse_id(self, device_id):
        self.dev_origin = self.__get_id(device_id)
        interest_score = 0
        summary = ""

        devices_address = []

        # for attribute in ["address", "name"]: # TODO name, ...
        for attribute in ["address", "name", "device_class", "manufacturer", "version", "hci_version", "lmp_version", "device_type", "device_id", "extra_hci_info"]: # TODO name, ...
            summary += f"\n\n--- PARSING {attribute.upper()} {self.dev_origin[attribute]} ---\n"
            devices = self.get_devices_by_attribute(attribute, dev_origin = self.dev_origin)
            if attribute == "address":
                devices_address = devices
            i_score, r_str  = self.__devices_comparison(devices, devices_address)
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

    def __devices_similarities(self, devices, original_devices = []):
        # find devices which could be the same but are not in original_devices (useful for reandom addresses)
        devices = [d for d in devices if d not in original_devices]
        # TODO compare all services with all from original_devices


    def __devices_comparison(self, devices: [BT_device], original_devices: [BT_device] = []):
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

DB_PATH = "../db.db"
db = DB(DB_PATH)

# TODO TESTING
bt = BT_stats(db)
# devices = bt.get_all_devices()
# device_ids = [d[0] for d in devices]
# for device_id in device_ids:
#     bt.parse_id(device_id)
#     if bt.interest_score > 0:
#         print(f"device id {device_id}: {bt.interest_score}")

# TODO only "important" parse_attr...
# TODO check rest if found devices are always same or if different devices have similar attributes (list original_devices(ids), mb save all lists, compare all)
print(bt.search_device("HUAWEI P30 Pro"))
bt.parse_id(50)

print(bt.interest_score)
print(bt.summary)
# bt.set_addr(addr)

# print(bt)


