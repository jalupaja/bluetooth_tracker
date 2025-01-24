import datetime

class BT_device:
    def __init__(self, struct):
        # input from database
        self.id = struct[0]
        self.address = struct[1]
        self.name = struct[2]
        self.device_class = struct[3]
        self.manufacturer = struct[4]
        self.version = struct[5]
        self.hci_version = struct[6]
        self.lmp_version = struct[7]
        self.device_type = struct[8]
        self.device_id = struct[9]
        self.extra_hci_info = struct[10]
        # TODO remove from scanner?/ add old_services parser
        # self.services = struct[11] # TODO

        self.timings = []
        self.services: [BT_service] = []

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


class BT_service:
    def __init__(self, struct):
        self.id = struct[0]
        self.host = struct[1]
        self.name = struct[2]
        self.service_classes = struct[3]
        self.profiles = struct[4]
        self.description = struct[5]
        self.provider = struct[6]
        self.service_id = struct[7]
        self.protocol = struct[8]
        self.port = struct[9]

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


