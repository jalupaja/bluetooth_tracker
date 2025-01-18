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
        for identifier in self.data['company_identifiers']:
            if identifier['value'] == value:
                return identifier['name']
        return value

    def parse(self, data):
        return [self.find_by_value(l) for l in data]

