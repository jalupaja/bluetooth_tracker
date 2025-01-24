import datetime
from bleak.backends.device import BLEDevice

from lib.manufacturers import Manufacturer
from lib.device_classes import CoD
from lib.log import log

class ble_device:
    def __init__(self, device):
        if isinstance(device, BLEDevice):
            self.__init_new_device(device)
        elif isinstance(device, tuple):
            self.__init_db_device(device)
        else:
            log.error("wrong input for ble_device")

    def __init_new_device(self, device):
        manufacturer = Manufacturer()

        self.details = device.details
        self.props = self.details['props']

        self.name = device.name
        self.name2 = self.__in_props("Name")
        self.address = device.address
        self.address2 = self.__in_props("Address")
        self.addresstype = self.__in_props("AddressType")
        self.alias = self.__in_props("Alias")
        self.appearance = self.__in_props("Appearance")
        self.paired = self.__in_props("Paired")
        self.bonded = self.__in_props("Bonded")
        self.trusted = self.__in_props("Trusted")
        self.blocked = self.__in_props("Blocked")
        self.servicedata = self.__in_props("ServiceData"),
        if self.servicedata and self.servicedata[0]:
            res = {}
            for k, v in self.servicedata[0].items():
                res[k] = str(v.hex())
            self.servicedata = str(res)
        else:
            self.servicedata = None
        self.advertisingflags = self.__in_props("AdvertisingFlags"),
        if self.advertisingflags and self.advertisingflags[0]:
            self.advertisingflags = self.advertisingflags[0].hex()
        else:
            self.advertisingflags = None
        self.advertisingdata = self.__in_props("AdvertisingData"),
        if self.advertisingdata and self.advertisingdata[0]:
            res = {}
            for k, v in self.advertisingdata[0].items():
                res[k] = str(v.hex())
            self.advertisingdata = str(res)
        else:
            self.advertisingdata = None
        self.legacypairing = self.__in_props("LegacyPairing")
        self.rssi = self.__in_props("RSSI")
        self.connected = self.__in_props("Connected")
        self.uuids = self.__in_props("UUIDs")
        if self.uuids is not None:
            self.uuids = ",".join(self.uuids)
        manu_data = self.__in_props("ManufacturerData")
        self.manufacturers = None
        self.manufacturer_binary = None
        if manu_data is not None:
            self.manufacturers = ",".join([str(s) for s in manufacturer.parse(manu_data)])
            self.manufacturer_binary = ",".join([b.hex() for b in list(manu_data.values())])
        self.txpower = self.__in_props("TxPower")
        self.servicesresolved = self.__in_props("ServicesResolved")
        self.class_of_device = self.__in_props("Class")
        self.modalias = self.__in_props("Modalias")
        self.icon = self.__in_props("Icon")
        self.timestamp = datetime.datetime.now().replace(microsecond=0) # timestamp in seconds
        self.geolocation = None

        self.props = self.details['props']

        done_props = "Class", "Modalias", "Icon", "Name", "Address", "AddressType", "Alias", "Appearance", "Paired", "Bonded", "Trusted", "Blocked", "LegacyPairing", "RSSI", "Connected", "UUIDs", "ManufacturerData", "ServiceData", "AdvertisingFlags", "AdvertisingData", "TxPower", "ServicesResolved", "Adapter"

        missing_props = [p for p in self.props if p not in done_props]
        if missing_props:
            log.warning(f"MISSED PROPS({self.address}): {missing_props}.")
        if self.name != None and self.name2 != None and self.name != self.name2:
            log.warning(f"Names don't match: {self.name} - {self.name2}")
        if self.address != None and self.address2 != None and self.address != self.address2:
            log.warning(f"Addresses don't match: {self.address} - {self.address2}")

        self.device_type = self.__parse_device_type()

    def __in_props(self, search):
        if self.props != None and search in self.props:
            return self.props[search]
        else:
            return None

    def __init_db_device(self, struct):
        (
            self.id, self.name, self.name2, self.address, self.address2, self.addresstype,
            self.alias, self.appearance, self.paired, self.bonded, self.trusted, self.blocked, self.legacypairing,
            self.connected, self.uuids, self.manufacturers, self.manufacturer_binary, self.servicedata,
            self.advertisingflags, self.advertisingdata, self.txpower, self.servicesresolved, self.class_of_device, self.modalias,
            self.icon
        ) = struct

        # Handle special cases for specific attributes
        if self.manufacturer_binary == "(None,)":
            self.manufacturer_binary = None

        if self.servicedata == "(None,)":
            self.servicedata = None

        self.timings = []
        self.services: [BT_service] = []

        self.device_type = self.__parse_device_type()

    def get_attributes(self):
        return ["name", "name2", "address", "address2", "addresstype", "alias", "appearance", "legacypairing", "uuids", "manufacturers", "manufacturer_binary", "servicedata", "advertisingflags", "advertisingdata", "servicesresolved", "class_of_device", "modalias", "icon"]

    def __parse_device_type(self):
        """
        Parse the device type using information gathered from the device
        sources:
            https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-cdp/77b446d0-8cea-4821-ad21-fabdf4d9a569?redirectedfrom=MSDN
        """

        if self.manufacturer_binary and len(self.manufacturer_binary) >= 4:
            # TODO rename
            manu_nibble = self.manufacturer_binary[0:2]
            manu_nibble_2 = self.manufacturer_binary[0:2]
            if self.manufacturers == "Apple, Inc.":
                if manu_nibble in ["12", "07"]:
                    return "Apple AirTag"
                elif manu_nibble == "02":
                    return "Mac"
                elif manu_nibble_2 == "06":
                    return "IPhone"
                elif manu_nibble_2 == "07":
                    return "IPad"

            if self.manufacturers == "Microsoft":
                if manu_nibble_2 == "09":
                    return "Windows Desktop"
                elif manu_nibble_2 in ["0a"]:
                    return "Windows Phone"
                elif manu_nibble_2 in ["0c"]:
                    return "Windows IoT"
                elif manu_nibble_2 in ["0d"]:
                    return "Surface Hub"
                elif manu_nibble_2 in ["0e"]:
                    return "Windows laptop"
                elif manu_nibble_2 in ["0f"]:
                    return "Windows tablet"

        if self.class_of_device:
            cod_string = CoD().parse(self.class_of_device)[0]
            if cod_string:
                return cod_string

        if self.icon == "phone":
            return "Phone"
        elif self.icon == "computer":
            return "Computer"
        elif self.icon in ["audio-headset", "audio-headphones"]:
            return "Headphones"
        elif self.icon == "audio-card":
            return "Audio card"
        elif self.icon == "input-mouse":
            return "Mouse"
        elif self.icon == "printer":
            return "Printer"
        elif self.icon == "input-keyboard":
            return "Keyboard"

    def __getitem__(self, item):
        # not nice but makes things so much easier
        return eval(f"self.{item}")

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

    def to_dict(self):
        res = {}
        for a in self.get_attributes():
            res[a] = self[a]
        return res

    def print(self):
        print(self)
