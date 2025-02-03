import datetime
from lib.ieee import IEEE

class bt_device:
    ieee = IEEE()
    def __init__(self, device):
        # input from database
        self.id = device[0]
        self.address = device[1]
        self.name = device[2]
        self.device_class = device[3]
        self.manufacturer = device[4]
        self.version = device[5]
        self.hci_version = device[6]
        self.lmp_version = device[7]
        self.device_type = device[8]
        self.device_id = device[9]
        self.extra_hci_info = device[10]
        self.timestamp = str(datetime.datetime.now().replace(microsecond=0)) # timestamp in seconds
        self.geolocation = None

        self.timings = []
        self.services: [BT_service] = []

    def update_manufacturer(self):
        if not self.manufacturer or self.manufacturer == "":
            res = self.parse_manufacturer()
            if res:
                self.manufacturer = res

    def parse_manufacturer(self):
        return self.ieee.search_address(self.address)

    def __getitem__(self, item):
        # not nice but makes things so much easier
        return eval(f"self.{item}")

    def get_attributes(self):
        return ["address", "name", "device_class", "manufacturer", "version", "hci_version", "lmp_version", "device_type", "device_id", "extra_hci_info"]

    def __parse_timings(self, timings):
        ret = []
        for t in timings:
            time = datetime.datetime.strptime(t[0], "%Y-%m-%d %H:%M:%S")
            geo = t[1]
            ret.append((time, geo))

        return ret

    def add_timings(self, timings):
        self.timings = self.__parse_timings(timings)

    def add_services(self, services):
        self.services = services

    # TODO -> rename...
    def add_services_timings(self, services, svc_timings):
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

class BT_service:
    def __init__(self, service):
        self.id = service[0]
        self.host = service[1]
        self.name = service[2]
        self.service_classes = service[3]
        self.profiles = service[4]
        self.description = service[5]
        self.provider = service[6]
        self.service_id = service[7]
        self.protocol = service[8]
        self.port = service[9]

        self.timings = []

    def __getitem__(self, item):
        # not nice but makes things so much easier
        return eval(f"self.{item}")

    def __eq__(self, other):
        return self.id == other.id

    def get_attributes(self):
        return ["host", "name", "service_classes", "profiles", "description", "provider", "service_id", "protocol", "port"]

    def __str__(self):
        ret_str = ""
        for attr in self.get_attributes():
            ret_str += f"{attr}: {self[attr]}\n"
        return ret_str
