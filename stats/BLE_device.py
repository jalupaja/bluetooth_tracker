import datetime

class BLE_device:
    def __init__(self, struct):
        (
            self.id, self.name, self.name2, self.address, self.address2, self.addresstype,
            self.alias, self.paired, self.bonded, self.trusted, self.blocked, self.legacypairing,
            self.connected, self.uuids, self.manufacturers, self.manufacturer_binary, self.servicedata,
            self.advertisingflags, self.txpower, self.servicesresolved, self.class_name, self.modalias,
            self.icon, self.appearance
        ) = struct

        # Handle special cases for specific attributes
        if self.manufacturer_binary == "(None,)":
            self.manufacturer_binary = None

        if self.servicedata == "(None,)":
            self.servicedata = None

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

