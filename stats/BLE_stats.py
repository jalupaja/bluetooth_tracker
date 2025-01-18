import numpy as np
import pandas as pd
from datetime import datetime
from difflib import SequenceMatcher
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

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
            ("icon", 0.7, Similarity.text),
            ]

    def get_all_devices(self):
        return pd.Series(self.db.execute(f"SELECT id, name, address FROM {self.TBL_DEV}")).unique()

    def find_most_seen_devices(self):
        res = self.db.execute(f"""
            SELECT ble_device.address, time.timestamp
            FROM {self.TBL_DEV_TIME}
            JOIN {self.TBL_DEV} ON ble_device_time.device_id = ble_device.id
            JOIN {self.TBL_TIME} ON ble_device_time.time_id = time.id
        """)
            # WHERE ble_device.addresstype = 'random';

        device_timestamps = defaultdict(list)
        for address, timestamp in res:
            device_timestamps[address].append(datetime.fromisoformat(timestamp))

        interesting_devices = []
        for address, timestamps in device_timestamps.items():
            timestamps.sort()
            if (timestamps[-1] - timestamps[0]).total_seconds() >= 60*60*24: # 24h
                interesting_devices.append(address)

        return interesting_devices

    def search_device(self, search):
        return pd.Series(self.db.execute(f"SELECT id, name, address FROM {self.TBL_DEV} WHERE name LIKE '%{search}%'")).unique()

    def get_device(self, device_id):

        res = self.db.execute(f"SELECT * FROM {self.TBL_DEV} WHERE id = '{device_id}'")

        if len(res) <= 0:
            return None

        dev = BLE_device(res[0])

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
            devices.append(self.get_device(dev_id))

        return devices

    def calculate_similarity_from_attributes(self, original_attributes, random_device):
        similarity_score = 0
        total_weight = 0

        for attr, weight, checker_fun in self.attributes:
            if attr in original_attributes and getattr(random_device, attr, None) is not None:
                similarity_score += weight * Similarity.calculate_similarity(original_attributes[attr], random_device[attr], checker_fun)
                total_weight += weight

        return similarity_score / total_weight if total_weight > 0 else 0

    def find_similar_devices(self, device_id, chunk_size=100, similarity_threshold=0.6, max_workers=8):
        def get_db_connection():
            return DB(self.db.path)

        def process_chunk(chunk_offset):
            local_db = get_db_connection()

            random_devices_data = local_db.execute(
                f"""
                SELECT * FROM {self.TBL_DEV}
                LIMIT {chunk_size} OFFSET {chunk_offset}
                """
            )
            # TODO WHERE id NOT IN ({','.join(str(d.id) for d in original_devices)})

            likely_matches_chunk = []
            for device_data in random_devices_data:
                random_device = BLE_device(device_data)

                similarity_sum = 0
                for original_attributes in original_unique_attributes:

                    similarity = self.calculate_similarity_from_attributes(
                        original_attributes, random_device
                    )
                    similarity_sum += similarity

                if similarity_sum >= similarity_threshold:
                    likely_matches_chunk.append((random_device.id, similarity_sum))
                    # print(f"Likely match found: Device ID = {random_device.id}, Similarity = {similarity_sum:.2f}")

            return likely_matches_chunk

        original_device = self.get_device(device_id)
        original_devices = self.get_devices_by_attribute("address", original_device.address)

        print(f"found {len(original_devices)} devices with the same address as {device_id}")

        original_unique_attributes = [
            {attr: dev[attr] for attr, _, _ in self.attributes if dev[attr] is not None}
            for dev in original_devices
        ]

        likely_matches = []
        offset = 0

        total_rows = self.db.execute(
            f"""
            SELECT COUNT(*) FROM {self.TBL_DEV}
            """
            # WHERE id NOT IN ({','.join(str(d.id) for d in original_devices)})
        )[0][0]

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            offsets = range(0, total_rows, chunk_size)

            test = process_chunk(offsets[0])

            futures = [executor.submit(process_chunk, offset) for offset in offsets]

            for future in futures:
                likely_matches.extend(future.result())

        likely_matches = sorted(likely_matches, key=lambda x: x[1], reverse=True)
        if len(likely_matches) == 0:
            print(f"Found no likely matches")
        else:
            print(f"Found {len(likely_matches) - len(original_devices)} likely matches.")

        return likely_matches

    def check_similar_devices(self, device_id, chunk_size=100, similarity_threshold=1.0, max_workers=8):
        def get_db_connection():
            return DB(self.db.path)

        def process_chunk(chunk_offset):
            local_db = get_db_connection()

            random_devices_data = local_db.execute(
                f"""
                SELECT * FROM {self.TBL_DEV}
                LIMIT {chunk_size} OFFSET {chunk_offset}
                """
            )
            # TODO WHERE id NOT IN ({','.join(str(d.id) for d in original_devices)})

            likely_matches_chunk = []
            for device_data in random_devices_data:
                random_device = BLE_device(device_data)

                similarity_sum = 0
                for original_attributes in original_unique_attributes:

                    similarity = self.calculate_similarity_from_attributes(
                        original_attributes, random_device
                    )
                    similarity_sum += similarity

                if similarity_sum >= similarity_threshold:
                    likely_matches_chunk.append((random_device.id, similarity_sum))
                    # print(f"Likely match found: Device ID = {random_device.id}, Similarity = {similarity_sum:.2f}")

            return likely_matches_chunk

        original_device = self.get_device(device_id)
        original_devices = self.get_devices_by_attribute("address", original_device.address)

        original_unique_attributes = [
            {attr: dev[attr] for attr, _, _ in self.attributes if dev[attr] is not None}
            for dev in original_devices
        ]

        likely_matches = []
        offset = 0

        total_rows = self.db.execute(
            f"""
            SELECT COUNT(*) FROM {self.TBL_DEV}
            """
            # WHERE id NOT IN ({','.join(str(d.id) for d in original_devices)})
        )[0][0]

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            offsets = range(0, total_rows, chunk_size)

            test = process_chunk(offsets[0])

            futures = [executor.submit(process_chunk, offset) for offset in offsets]

            for future in futures:
                likely_matches.extend(future.result())

        likely_matches = sorted(likely_matches, key=lambda x: x[1], reverse=True)

        return len(likely_matches) - len(original_devices), [d.id for d in original_devices]

    def find_interesting_random_devices(self, chunk_size=100, similarity_threshold=0.6, max_workers=8):
        devices = self.db.execute(f"SELECT id,manufacturers FROM {self.TBL_DEV} WHERE addresstype = 'random'")

        covered_devices = []
        devices = [d[0] for d in devices]
        for d in devices: # this could exclude some but this just takes too long
            if d in covered_devices \
                or self.get_device(d).manufacturers == "Apple, Inc.": # Apple has way too many...
                continue

            check, devs = self.check_similar_devices(d, chunk_size, similarity_threshold, max_workers)
            covered_devices = covered_devices + devs
            if check > 0:
                print(f"{d}\t{check}")

    def print_all_timings(self, devices):
        timings = []
        for device in devices:
            for timing in device.timings:
                timings.append((device.address, timing))

        timings.sort(key=lambda x: x[1])

        print(f"TIMINGS FOR {len(devices)} DEVICES:")
        for address, timing in timings:
            print(f"Device ID: {address}: {timing}")

    def print_timings(self, devices):
        device_timings = []
        for device in devices:
            d_min, d_max = device.get_timings_minmax()
            if d_min is not None:
                device_timings.append((device, d_min, d_max))

        device_timings.sort(key=lambda x: x[1])
        if len(devices) > 1:
            print(f"TIMINGS FOR {len(devices)} DEVICES FROM {device_timings[0][1]} TO {device_timings[-1][2]}:")

        for device, d_min, d_max in device_timings:
            if len(device.timings) == 1:
                print(f"Device ID: {device.address} on {d_max}")
            else:
                print(f"Device ID: {device.address} on {d_min} - {d_max} ({len(device.timings)} times in a span of {d_max - d_min})")

    def print_unique_attrs(self, devices):
        unique_attrs = {attr: {} for attr, _, _ in self.attributes}

        for device in devices:
            for attr, _, _ in self.attributes:
                value = device[attr]
                if value is not None:
                    if value not in unique_attrs[attr]:
                        unique_attrs[attr][value] = []
                    unique_attrs[attr][value].append(device.id)

        for attr, values in unique_attrs.items():
            if not values:
                continue

            print(f"\033[1m{attr.upper()}:\033[0m")
            color = "\033[92m" if len(values) <= 1 else "\033[91m"  # green: equal, red: different
            for value, device_ids in values.items():
                device_ids_str = ", ".join(map(str, device_ids))
                print(f"\t{color}{value} \033[0m({device_ids_str})")
            print()

    def __get_color(self, similarity):
        red = int((1 - similarity) * 255)
        green = int(similarity * 255)
        return f"\033[38;2;{red};{green};0m"

    def compare_devices(self, device_id1, device_id2):
        d1 = self.get_device(device_id1)
        d2 = self.get_device(device_id2)

        print(f"Comparing {device_id1} - {device_id2}")

        self.print_timings([d1, d2])
        # self.print_all_timings([d1, d2])

        for attr, weight, checker_fun in self.attributes:
            value1 = d1[attr]
            value2 = d2[attr]
            similarity = Similarity.calculate_similarity(value1, value2, checker_fun)
            color = self.__get_color(similarity)
            print(f"{color}{attr.upper()}> {value1} - {value2}\n\033[0m")

    def compare_devices_groups(self, device_id1, device_id2):
        devices_group1 = self.get_devices_by_attribute("address", dev_origin=self.get_device(device_id1))
        devices_group2 = self.get_devices_by_attribute("address", dev_origin=self.get_device(device_id2))

        if not devices_group1:
            print(f"The first group was not found!")
            return
        if not devices_group2:
            print(f"The second group was not found!")
            return

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
                    color = self.__get_color(similarity)
                    print(f"{color}{attr.upper()}> {value1} - {value2} | Similarity: {similarity:.2f}\n\033[0m")

        self.print_all_timings(devices_group1 + devices_group2)

    def get_devices(self, ids):
        return [self.get_device(i) for i in ids]

# TODO original... servicedata is string? should be like manu_binary
# TODO fix list comparison. should compare per item. if not exists, should use None for instance (UUIDS!!!)
# TODO TESTING
DB_PATH = "../db/db.db"
db = DB(DB_PATH)

ble = BLE_stats(db)
# DB_PATH = "../db/2024.db"
# [print(b) for b in ble.search_device("Apple")]
# results = ble.find_similar_devices(device_id=23453)
# result = ble.find_similar_devices(8102, similarity_threshold=1.0)
# result = ble.find_similar_devices(18656, similarity_threshold=1.0)
# ids = [r[0] for r in result]
# interesting_devices = [ble.get_device(i) for i in ids[0:30]]
# ble.print_unique_attrs(interesting_devices)

# DB_PATH = "../db/38c3.db"
# devices = ble.find_interesting_devices()
# devices = ble.get_all_devices()
# device_ids = [d[0] for d in devices]
# summaries = []
# for device_id in device_ids:
#     ble.parse_id(device_id)
#     summaries.append(ble.summary)
#     if ble.interest_score > 4:
#         print(f"device id {device_id}: {ble.interest_score}")
dev = ble.find_similar_devices(69179, similarity_threshold=0.15)
# dev = ble.find_similar_devices(25501, similarity_threshold=0.30)
# devices = [ble.get_device(d[0]) for d in dev]
# ble.print_all_timings(devices)
# print(ble.get_device(25501))

# dev = [ble.get_devices_by_attribute("address", d) for d in devices_in_2_places]
# ids = [[d.id for d in x] for x in dev]
# ids_in_3_places
