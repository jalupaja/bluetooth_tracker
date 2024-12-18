import datetime

class BLE_device:
    def __init__(self, struct):
        self.id = struct[0]
        self.name = struct[1]
        self.name2 = struct[2]
        self.address = struct[3]
        self.address2 = struct[4]
        self.addresstype = struct[5]
        self.alias = struct[6]
        self.appearance = struct[7]
        self.paired = struct[8]
        self.bonded = struct[9]
        self.trusted = struct[10]
        self.blocked = struct[11]
        self.legacypairing = struct[12]
        self.connected = struct[13]
        self.uuids = struct[14]
        self.manufacturers = struct[15]
        if struct[16] == "(None,)":
            self.manufacturer_binary = None
        else:
            self.manufacturer_binary = struct[16]
        if struct[17] == "(None,)":
            self.servicedata  = None
        else:
            self.servicedata = struct[17]
        self.txpower = struct[18]
        self.advertisingflags = struct[19]
        self.servicesresolved = struct[20]
        self.class_name = struct[21]
        self.modalias = struct[22]
        self.icon = struct[23]

        self.timings = []
        self.services: [BT_service] = []

    def __getitem__(self, item):
        # not nice but makes things so much easier
        return eval(f"self.{item}")

    def get_attributes(self):
        return ["name", "name2", "address", "address2", "addresstype", "alias", "appearance", "legacypairing", "uuids", "manufacturers", "manufacturer_binary", "servicedata", "advertisingflags", "servicesresolved", "class_name", "modalias", "icon"]

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

