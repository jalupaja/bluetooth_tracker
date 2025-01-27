import numpy as np
import pandas as pd

# import requests
# import re

def maclookupAPI(address):
    uri = "https://api.maclookup.app/v2/macs/"

    address = address.replace(":", ".").replace("-", ".")

    n_uri = f"{uri}{address}"

    res = requests.get(n_uri)
    if res.status_code == 200:
        return res.json()
    else:
        print(f"ERROR: {res.text}")
        return None

class IEEE:
    _instance = None
    folder = "Assigned Numbers/IEEE"
    # MAC Address Block sizes: large, medium, small
    file_large = f"{folder}/oui.csv"
    file_medium = f"{folder}/mam.csv"
    file_small = f"{folder}/oui36.csv"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.data = pd.concat([self.__load_csv(self.file_large),
                               self.__load_csv(self.file_medium),
                               self.__load_csv(self.file_small),
                               ])
        self.lens = sorted({len(a) for a in self.data['Assignment']}, reverse = True)

    def __load_csv(self, file):
        return pd.read_csv(file)

    def search_address(self, address):
        # search for address, return company name
        address = address.replace(":", "").replace("-", "")
        for l in self.lens:
            addr_part = address[0:l]
            res = self.data[self.data['Assignment'] == addr_part]
            if len(res) > 0:
                return res['Organization Name'].iloc[0]

    def search_company(self, company):
        # search for company name
        return self.data[self.data['Organization Name'].str.contains(company) == True]

