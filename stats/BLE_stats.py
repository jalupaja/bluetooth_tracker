import numpy as np
import pandas as pd
from difflib import SequenceMatcher
from collections import defaultdict

from BLE_device import BLE_device
from db import DB
from Similarity import Similarity

class BLE_stats:
    TBL_TIME = "time"
    TBL_DEV = "ble_device"
    TBL_DEV_TIME = "ble_device_time"

    interest_score = -1
    summary = None

    none_values = [
            None,
            """
Requesting information ...""",
            ]

    attributes = []

    def __init__(self, db, device_id = None):
        self.db = db
        if device_id is not None:
            self.parse_id(device_id)

        self.TBL_DEV_names = self.db.get_columns(self.TBL_DEV)
        # self.TBL_SVC_names = self.db.get_columns(self.TBL_SVC)

        # Attributes, weight
        # TODO better weighting (using ML)
        # -> save to list, list into ML-Model?
        self.attributes = [
            ("name", 0.2, Similarity.text),
            ("name2", 0.2, Similarity.text),
            ("address", 10, Similarity.exact),
            ("address2", 10, Similarity.exact),
            ("addresstype", 0.0, Similarity.exact),
            ("alias", 0.7, Similarity.text),
            ("appearance", 0.3, Similarity.numeric),
            ("legacypairing", 0.5, Similarity.numeric),
            ("uuids", 1.0, None), # TODO
            ("manufacturers", 0.7, None), # TODO
            ("manufacturer_binary", 0.9, None), # TODO has to be actual bytes!!!
            ("servicedata", 0.6, None), # TODO should be binary. current is str(binary...)
            ("advertisingflags", 0.4, None), # TODO
            ("servicesresolved", 0.2, None), # TODO
            ("class_name", 0.3, Similarity.text),
            ("modalias", 0.6, Similarity.text),
            ("icon", 0.7, None),
            ]

    def get_all_devices(self):
        return pd.Series(self.db.execute(f"SELECT id, name, address FROM {self.TBL_DEV}")).unique()

    def search_device(self, search):
        return pd.Series(self.db.execute(f"SELECT id, name, address FROM {self.TBL_DEV} WHERE name LIKE '%{search}%'")).unique()

    def parse_id(self, device_id):
        self.dev_origin = self.__get_id(device_id)
        interest_score = 0
        summary = ""

        devices_address = []

        for attribute in ["address", "name", ]: # TODO use more
            summary += f"\n\n--- PARSING {attribute.upper()} {self.dev_origin[attribute]} ---\n"
            devices = self.get_devices_by_attribute(attribute, dev_origin = self.dev_origin)
            if attribute == "address":
                devices_address = devices
            i_score, r_str = 0, "" # TODO
            interest_score += i_score
            summary += r_str


        self.interest_score = interest_score
        self.summary = summary

    def __get_id(self, device_id):

        dev = BLE_device(
                self.db.execute(f"SELECT * FROM {self.TBL_DEV} WHERE id = '{device_id}'")[0]
                )

        dev.add_timings(self.db.execute(f"""SELECT t.timestamp, t.geolocation FROM {self.TBL_TIME} t
                            INNER JOIN {self.TBL_DEV_TIME} dt ON t.id = dt.time_id
                            WHERE dt.device_id = {device_id}
                            """))

        return dev

    def get_devices_by_attribute(self, attribute, val = None, dev_origin: BLE_device = None):
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

    def calculate_similarity_from_attributes(self, original_attributes, random_device):
        similarity_score = 0
        total_weight = 0

        for attr, weight, checker_fun in self.attributes:
            if attr in original_attributes and getattr(random_device, attr, None) is not None:
                similarity_score += weight * Similarity.calculate_similarity(original_attributes[attr], random_device[attr], checker_fun)
                total_weight += weight

        return similarity_score / total_weight if total_weight > 0 else 0

    def find_similar_devices(self, device_id, chunk_size=100, similarity_trashold=1.0):
        original_device = self.__get_id(device_id)

        original_devices = self.get_devices_by_attribute("address", original_device.address)

        print(f"found {len(original_devices)} devices with the same address as {device_id}")

        original_unique_attributes = [
            {attr: dev[attr] for attr, _, _ in self.attributes if dev[attr] is not None}
            for dev in original_devices
        ]

        likely_matches = []
        offset = 0

        while True:
            # WHERE addresstype = 'random' AND id NOT IN ({','.join(str(d.id) for d in original_devices)})
            random_devices_data = self.db.execute(
                f"""
                SELECT * FROM {self.TBL_DEV}
                WHERE id NOT IN ({','.join(str(d.id) for d in original_devices)})
                LIMIT {chunk_size} OFFSET {offset}
                """
            )

            if not random_devices_data:
                break

            random_devices = [BLE_device(device_data) for device_data in random_devices_data]

            for random_device in random_devices:
                similarity_sum = 0
                for original_attributes in original_unique_attributes:
                    similarity = self.calculate_similarity_from_attributes(
                        original_attributes, random_device
                    )
                    similarity_sum += similarity

                if similarity_sum >= similarity_trashold:
                    likely_matches.append((random_device.id, similarity_sum))
                    print(f"Likely match found: Device ID = {random_device.id}, Similarity = {similarity_sum:.2f}")

            offset += chunk_size

        return sorted(likely_matches, key=lambda x: x[1], reverse=True)

    def print_timings(self, devices):
        for device in devices:
            d_min, d_max = device.get_timings_minmax()
            print(f"Device ID {device.id} ")
            if len(device.timings) == 1:
                print(f"timings:\n\ton {d_max}\n")
            else:
                print(f"timings:\n\ton {d_min} - {d_max} "
                      f"({len(device.timings)} times in a span of {d_max - d_min})\n")


    def print_unique_attrs(self, devices):
        def colorize_equal(value, is_equal):
            if is_equal:
                return f"\033[92m{value}\033[0m" # green
            else:
                return f"\033[91m{value}\033[0m" # red

        attr_values = {attr: defaultdict(list) for attr, _, _ in self.attributes}

        for device in devices:
            for attr, _, _ in self.attributes:
                value = device[attr]
                if value is not None:
                    attr_values[attr][value].append(device.id)

        for attr, values in attr_values.items():
            print(f"{attr.upper()}:")
            is_equal = len(values) == 1  # TODO Check if all values are the same
            for value, device_ids in values.items():
                colored_value = colorize_equal(value, is_equal)
                print(f"\t{colored_value} ({', '.join(map(str, device_ids))})")
            print()

    def compare_devices(self, device_id1, device_id2):
        d1 = self.get_device(device_id1)
        d2 = self.get_device(device_id2)

        def __get_color(similarity):
            red = int((1 - similarity) * 255)
            green = int(similarity * 255)
            return f"\033[38;2;{red};{green};0m"

        print(f"Comparing {device_id1} - {device_id2}")

        def print_timings(device):
            d_min, d_max = device.get_timings_minmax()
            if len(device.timings) == 1:
                print(f"\ton {d_max}\n")
            else:
                print(f"\ton {d_min} - {d_max} ({len(device.timings)} times in a span of {d_max - d_min})\n")

        print_timings(d1)
        print("----")
        print_timings(d2)

        for attr, weight, checker_fun in self.attributes:
            value1 = d1[attr]
            value2 = d2[attr]
            similarity = Similarity.calculate_similarity(value1, value2, checker_fun)
            color = __get_color(similarity)
            print(f"{color}{attr.upper()}> {value1} - {value2}\n\033[0m")

    def compareDevicesGroups(self, device_id1, device_id2):
        # TODO combine with above function (cleanup)?
        devices_group1 = self.get_devices_by_attribute("address", dev_origin=self.__get_id(device_id1))
        devices_group2 = self.get_devices_by_attribute("address", dev_origin=self.__get_id(device_id2))

        def __get_color(similarity):
            red = int((1 - similarity) * 255)
            green = int(similarity * 255)
            return f"\033[38;2;{red};{green};0m"

        print(f"Comparing unique values between device groups for IDs {device_id1} and {device_id2}")

        unique_values_group1 = {attr: set() for attr, _, _ in self.attributes}
        unique_values_group2 = {attr: set() for attr, _, _ in self.attributes}

        for device in devices_group1:
            for attr, _, _ in self.attributes:
                value = device[attr]
                if value is not None:
                    unique_values_group1[attr].add(value)

        for device in devices_group2:
            for attr, _, _ in self.attributes:
                value = device[attr]
                if value is not None:
                    unique_values_group2[attr].add(value)

        for attr, weight, checker_fun in self.attributes:
            values_group1 = list(unique_values_group1[attr])
            values_group2 = list(unique_values_group2[attr])

            for value1 in values_group1:
                for value2 in values_group2:
                    similarity = Similarity.calculate_similarity(value1, value2, checker_fun)
                    color = __get_color(similarity)
                    print(f"{color}{attr}> {value1} - {value2} | Similarity: {similarity:.2f}\n\033[0m")

# TODO write colored helper function to compare 2 devices
def print_dev(device_id):
    print(BLE_stats(db, device_id).dev_origin)

def print_results(results):
    for r in results:
        print_dev(r[0])

# TODO original... servicedata is string? should be like manu_binary
# TODO manufactuerers, uuids getauscht?
# TODO TESTING
DB_PATH = "../db.db"
db = DB(DB_PATH)

ble_stats = BLE_stats(db)
# [print(b) for b in ble_stats.search_device("Apple")]
# results = ble_stats.find_similar_devices(device_id=23453)
res = ble_stats.find_similar_devices(18656, similarity_trashold=1.0)
# TODO could be paralized...
# ble_stats.compareDevices(18656, 570)
