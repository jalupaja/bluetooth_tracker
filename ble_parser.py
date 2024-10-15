from manufacturers import Manufacturer

class BLE_Parser:
    manufacturer = Manufacturer()

    device = None
    details = None
    props = None

    name = None
    name2 = None
    path = None
    address = None
    address2 = None
    addresstype = None
    alias = None
    paired = None
    bonded = None
    trusted = None
    blocked = None
    legacypairing = None
    rssi = None
    connected = None
    uuids = None
    adapter = None
    manufacturers = None
    manufacturer_binary = None
    txpower = None
    servicesresolved = None
    class_name = None
    modalias = None
    icon = None

    def __init__(self, device):
        self.device = device
        self.details = device.details
        self.props = self.details['props']
        self.__parse()

    def __parse(self):
        if self.device and self.details and self.props:
            self.address = self.device.address
            self.name = self.device.name
            self.path = self.details['path']

            self.name2 = self.__in_props("Name")
            self.address2 = self.__in_props("Address")
            self.addresstype = self.__in_props("AddressType")
            self.alias = self.__in_props("Alias")
            self.paired = self.__in_props("Paired")
            self.bonded = self.__in_props("Bonded")
            self.trusted = self.__in_props("Trusted")
            self.blocked = self.__in_props("Blocked")
            self.legacypairing = self.__in_props("LegacyPairing")
            self.rssi = self.__in_props("RSSI")
            if self.rssi:
                self.rssi = ",".join(self.rssi)
            self.connected = self.__in_props("Connected")
            self.uuids = self.__in_props("UUIDs")
            self.adapter = self.__in_props("Adapter")
            self.class_name = self.__in_props("Class")
            self.modalias = self.__in_props("Modalias")
            self.icon = self.__in_props("Icon")

            manu_data = self.__in_props("ManufacturerData")
            if (manu_data is not None):
                self.manufacturers = ",".join(self.manufacturer.parse(manu_data))
                self.manufacturer_binary = ",".join([b for b in list(manu_data.values())])
            self.txpower = self.__in_props("TxPower")
            self.servicesresolved = self.__in_props("ServicesResolved")

            done_props = "Class", "Modalias", "Icon", "Name", "Address", "AddressType", "Alias", "Paired", "Bonded", "Trusted", "Blocked", "LegacyPairing", "RSSI", "Connected", "UUIDs", "Adapter", "ManufacturerData", "TxPower", "ServicesResolved",

            missing_props = [p for p in self.props if p not in done_props]
            if missing_props:
                print(f"MISSED PROPS({self.address}): {missing_props}")
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
        print(f"\tadapter: \t\t{self.adapter}")
        print(f"\tmanufacturers: \t\t{self.manufacturers}")
        print(f"\tmanufacturer_binary: \t{self.manufacturer_binary}")
        print(f"\ttxpower: \t\t{self.txpower}")
        print(f"\tservicesresolved: \t{self.servicesresolved}")
        print(f"\tclass: \t\t\t{self.class_name}")
        print(f"\tmodalias: \t\t{self.modalias}")
        print(f"\ticon: \t\t\t{self.icon}")

        print()





