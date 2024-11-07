from manufacturers import Manufacturer
import datetime

import random
import pickle


rnd = random.Random()
def export_object(obj):
    file_name = f"export_{rnd.randint(0, 1000)}.pk1"
    with open(file_name, 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
    return file_name

def import_object(file_name):
    with open(file_name, 'rb') as f:
        return pickle.load(f)


class BLE_Parser:
    manufacturer = Manufacturer()

    device = None
    details = None
    props = None

    name = None
    name2 = None
    address = None
    address2 = None
    addresstype = None
    alias = None
    paired = None
    bonded = None
    trusted = None
    blocked = None
    servicedata = None,
    advertisingflags = None,
    legacypairing = None
    rssi = None
    connected = None
    uuids = None
    manufacturers = None
    manufacturer_binary = None
    txpower = None
    servicesresolved = None
    class_name = None
    modalias = None
    icon = None

    timestamp = datetime.datetime.now()
    geolocation = "" # TODO current pc location (GPS/text input?) (if available)

    def __init__(self, device):
        self.device = device
        self.details = device.details
        self.props = self.details['props']
        self.__parse()

    def __parse(self):
        if self.device and self.details and self.props:
            self.address = self.device.address
            self.name = self.device.name

            self.name2 = self.__in_props("Name")
            self.address2 = self.__in_props("Address")
            self.addresstype = self.__in_props("AddressType")
            self.alias = self.__in_props("Alias")
            self.paired = self.__in_props("Paired")
            self.bonded = self.__in_props("Bonded")
            self.trusted = self.__in_props("Trusted")
            self.blocked = self.__in_props("Blocked")
            self.servicedata = self.__in_props("ServiceData")
            if self.servicedata is not None:
                self.servicedata = str(self.servicedata)
            self.advertisingflags  = self.__in_props("AdvertisingFlags")
            self.legacypairing = self.__in_props("LegacyPairing")
            self.rssi = self.__in_props("RSSI")
            self.connected = self.__in_props("Connected")
            self.uuids = self.__in_props("UUIDs")
            if self.uuids is not None:
                self.uuids = ",".join(self.uuids)
            self.class_name = self.__in_props("Class")
            self.modalias = self.__in_props("Modalias")
            self.icon = self.__in_props("Icon")

            manu_data = self.__in_props("ManufacturerData")
            if manu_data is not None:
                self.manufacturers = ",".join([str(s) for s in self.manufacturer.parse(manu_data)])
                self.manufacturer_binary = ",".join([b.hex() for b in list(manu_data.values())])
            self.txpower = self.__in_props("TxPower")
            self.servicesresolved = self.__in_props("ServicesResolved")

            done_props = "Class", "Modalias", "Icon", "Name", "Address", "AddressType", "Alias", "Paired", "Bonded", "Trusted", "Blocked", "LegacyPairing", "RSSI", "Connected", "UUIDs", "ManufacturerData", "ServiceData", "AdvertisingFlags", "TxPower", "ServicesResolved", "Adapter"

            missing_props = [p for p in self.props if p not in done_props]
            if missing_props:
                export_file = export_object(self.props)
                print(f"MISSED PROPS({self.address}): {missing_props}. \n\t\texported props to {export_file}")
            if self.name != None and self.name2 != None and self.name != self.name2:
                print(f"Names don't match: {self.name} - {self.name2}")
            if self.address != None and self.address2 != None and self.address != self.address2:
                print(f"Addresses don't match: {self.address} - {self.address2}")

    def __in_props(self, search):
        if self.props != None and search in self.props:
            return self.props[search]
        else:
            return None

    def print(self):

        print()
        print(f"{self.name} ({self.address})")
        print(f"\taddresstype: \t\t{self.addresstype}")
        print(f"\talias: \t\t\t{self.alias}")
        print(f"\tpaired: \t\t{self.paired}")
        print(f"\tbonded: \t\t{self.bonded}")
        print(f"\ttrusted: \t\t{self.trusted}")
        print(f"\tblocked: \t\t{self.blocked}")
        print(f"\tlegacypairing: \t\t{self.legacypairing}")
        print(f"\trssi: \t\t\t{self.rssi}")
        print(f"\tconnected: \t\t{self.connected}")
        print(f"\tuuids: \t\t\t{self.uuids}")
        print(f"\tmanufacturers: \t\t{self.manufacturers}")
        print(f"\tmanufacturer_binary: \t{self.manufacturer_binary}")
        print(f"\ttxpower: \t\t{self.txpower}")
        print(f"\tservicesresolved: \t{self.servicesresolved}")
        print(f"\tclass: \t\t\t{self.class_name}")
        print(f"\tmodalias: \t\t{self.modalias}")
        print(f"\ticon: \t\t\t{self.icon}")

        print()





