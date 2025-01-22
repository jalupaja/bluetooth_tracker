import datetime
from device_classes import CoD

class BLE_device:
    def __init__(self, struct):
        (
            self.id, self.name, self.name2, self.address, self.address2, self.addresstype,
            self.alias, self.appearance, self.paired, self.bonded, self.trusted, self.blocked, self.legacypairing,
            self.connected, self.uuids, self.manufacturers, self.manufacturer_binary, self.servicedata,
            self.advertisingflags, self.txpower, self.servicesresolved, self.class_of_device, self.modalias,
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

    def __parse_device_type(self):
        """
        Parse the device type using information gathered from the device
        sources:
            https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-cdp/77b446d0-8cea-4821-ad21-fabdf4d9a569?redirectedfrom=MSDN
        """
        if self.manufacturer_binary and len(self.manufacturer_binary) >= 4:
            # TODO rename
            manu_info = self.manufacturer_binary[0:2]
            manu_info_back = self.manufacturer_binary[0:2]
            if self.manufacturers == "Apple, Inc.":
                if manu_info in ["12", "07"]:
                    return "AirTag"
                elif manu_info == "02":
                    return "Mac"
                elif manu_info_back == "06":
                    return "IPhone"
                elif manu_info_back == "07":
                    return "IPad"

            elif self.manufacturers == "Microsoft":
                if manu_info_back == "01":
                    return "XBox"
                elif manu_info_back == "09":
                    return "Windows Desktop"
                elif manu_info_back in ["0a"]:
                    return "Windows Phone"
                elif manu_info_back in ["0c"]:
                    return "Windows IoT"
                elif manu_info_back in ["0d"]:
                    return "Surface Hub"
                elif manu_info_back in ["0e"]:
                    return "Windows laptop"
                elif manu_info_back in ["0f"]:
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

    def get_attributes(self):
        return ["name", "name2", "address", "address2", "addresstype", "alias", "appearance", "legacypairing", "uuids", "manufacturers", "manufacturer_binary", "servicedata", "advertisingflags", "servicesresolved", "class_of_device", "modalias", "icon"]

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

