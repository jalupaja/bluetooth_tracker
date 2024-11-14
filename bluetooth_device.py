import datetime

class BluetoothDevice:
    def __init__(self, address, name):
        self.address = address
        self.name = name
        self.device_class = None
        self.services = []
        self.rssi = None
        self.manufacturer = None
        self.version = None
        self.hci_version = None
        self.lmp_version = None
        self.device_type = None
        self.device_id = None
        self.extra_hci_info = None
        self.timestamp = str(datetime.datetime.now().replace(microsecond=0)) # timestamp in seconds
        self.geolocation = None # TODO current pc location (GPS/text input?) (if available)

    def update_device_class(self, device_class):
        self.device_class = device_class

    def add_service(self, service_info):
        self.services.append(service_info)

    def set_rssi(self, rssi):
        self.rssi = rssi

    def set_manufacturer(self, manufacturer):
        self.manufacturer = manufacturer

    def set_version(self, version):
        self.version = version

    def set_hci_version(self, hci_version):
        self.hci_version = hci_version

    def set_lmp_version(self, lmp_version):
        self.lmp_version = lmp_version

    def set_device_type(self, device_type):
        self.device_type = device_type

    def set_device_id(self, device_id):
        self.device_id = device_id

    def set_extra_hci_info(self, extra_hci_info):
        self.extra_hci_info = extra_hci_info

    def __str__(self):
        return f"Device Name: {self.name}\nDevice Address: {self.address}\nClass: {self.device_class}\nManufacturer: {self.manufacturer}\nVersion: {self.version}\nHCI Version: {self.hci_version}\nLMP Version: {self.lmp_version}\nDevice Type: {self.device_type}\nDevice ID: {self.device_id}\nRSSI: {self.rssi}\nExtra HCI info: {self.extra_hci_info}\nServices: {self.services}"

    def to_dict(self):
        """
        Converts the BluetoothDevice object to a dictionary format for easy export to a database.
        """
        return {
            'address': self.address,
            'name': self.name,
            'device_class': self.device_class,
            'manufacturer': self.manufacturer,
            'version': self.version,
            'hci_version': self.hci_version,
            'lmp_version': self.lmp_version,
            'device_type': self.device_type,
            'device_id': self.device_id,
            'rssi': self.rssi,
            'extra_hci_info': self.extra_hci_info,
            'services': self.services
        }


