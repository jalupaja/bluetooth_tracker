import yaml

class CoD: # Class of Device
    _instance = None
    yaml_file = "Assigned Numbers/class_of_device.yaml"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.data = self.__load_yaml(self.yaml_file)

    def __load_yaml(self, yaml_file):
        with open(yaml_file, 'r') as file:
            return yaml.safe_load(file)

    def parse_services(self, service_indices):
        res = []
        for service in self.data['cod_services']:
            if service['bit'] in service_indices:
                res.append(service['name'])
        return res

    def __parse_device_class(self, major, minor):
        try:
            major_data = self.data['cod_device_class'][major]
            minor_data = major_data['minor'][minor]

            # TODO create ret string
            major_string = major_data['name'].split(" (", 1)[0]
            minor_string = minor_data['name']
            return f"{major_string} {minor_string}"
        except (KeyError, ValueError):
            return None

    def parse(self, cod):
        cod=int(cod)
        binary_cod = f"{cod:024b}"

        minor = int(binary_cod[-8:-2], 2)
        major = int(binary_cod[-13:-8], 2)
        service_classes = ''.join(reversed(binary_cod))[-11:]
        service_indices = [i + 13 for i, bit in enumerate(service_classes) if bit == '1']

        return (self.__parse_device_class(major, minor), service_indices)

