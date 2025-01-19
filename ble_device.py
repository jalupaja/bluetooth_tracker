import datetime

from manufacturers import Manufacturer
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
            self.servicedata = str(self.servicedata)
        self.advertisingflags = self.__in_props("AdvertisingFlags"),
        if self.advertisingflags is not None:
            self.advertisingflags = str(self.advertisingflags)
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
        self.class_name = self.__in_props("Class")
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

    def __in_props(self, search):
        if self.props != None and search in self.props:
            return self.props[search]
        else:
            return None

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
        res += f"\tclass: \t\t\t{self.class_name}\n"
        res += f"\tmodalias: \t\t{self.modalias}\n"
        res += f"\ticon: \t\t\t{self.icon}\n"

        return res

    def print(self):
        print(self)


