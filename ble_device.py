import datetime

from manufacturers import Manufacturer
from device_classes import CoD
import log

class BleDevice:

    def __init__(self, device):
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
        if self.servicedata is not None:
            if self.servicedata[0]:
                res = {}
                for k, v in self.servicedata[0].items():
                    res[k] = str(v.hex())
                self.servicedata = str(res)
            else:
                self.servicedata = "None"
        self.advertisingflags = self.__in_props("AdvertisingFlags"),
        if self.advertisingflags is not None:
            self.advertisingflags = str(self.advertisingflags[0].hex())
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
        self.timestamp = str(datetime.datetime.now().replace(microsecond=0)) # timestamp in seconds
        self.geolocation = None # TODO current pc location (GPS/text input?) (if available)

        self.props = self.details['props']

        done_props = "Class", "Modalias", "Icon", "Name", "Address", "AddressType", "Alias", "Appearance", "Paired", "Bonded", "Trusted", "Blocked", "LegacyPairing", "RSSI", "Connected", "UUIDs", "ManufacturerData", "ServiceData", "AdvertisingFlags", "TxPower", "ServicesResolved", "Adapter"

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
                if manu_nibble_2 == "01":
                    return "XBox"
                elif manu_nibble_2 == "09":
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

    def __str__(self):
        res = ""
        res += f"{self.name} ({self.address})\n"
        res += f"\taddresstype: \t\t{self.addresstype}\n"
        res += f"\talias: \t\t\t{self.alias}\n"
        res += f"\tAppearance: \t\t{self.appearance}\n"
        res += f"\tpaired: \t\t{self.paired}\n"
        res += f"\tbonded: \t\t{self.bonded}\n"
        res += f"\ttrusted: \t\t{self.trusted}\n"
        res += f"\tblocked: \t\t{self.blocked}\n"
        res += f"\tlegacypairing: \t\t{self.legacypairing}\n"
        res += f"\trssi: \t\t\t{self.rssi}\n"
        res += f"\tconnected: \t\t{self.connected}\n"
        res += f"\tuuids: \t\t\t{self.uuids}\n"
        res += f"\tmanufacturers: \t\t{self.manufacturers}\n"
        res += f"\tmanufacturer_binary: \t{self.manufacturer_binary}\n"
        res += f"\ttxpower: \t\t{self.txpower}\n"
        res += f"\tservicesresolved: \t{self.servicesresolved}\n"
        res += f"\tclass: \t\t\t{self.class_of_device}\n"
        res += f"\tmodalias: \t\t{self.modalias}\n"
        res += f"\ticon: \t\t\t{self.icon}\n"

        return res

    def print(self):
        print(self)


