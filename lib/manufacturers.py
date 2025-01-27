import yaml

class Manufacturer:
    _instance = None
    yaml_file = "Assigned Numbers/company_identifiers.yaml"

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

    def find_by_value(self, value):
        if value:
            for identifier in self.data['company_identifiers']:
                if identifier['value'] == value:
                    return identifier['name']
        return None

    def parse(self, data):
        if data:
            if isinstance(data, str):
                data = data.split(",")
            res = [self.find_by_value(int(l)) for l in data]
            return ", ".join([r for r in res if r])
        else:
            return None

