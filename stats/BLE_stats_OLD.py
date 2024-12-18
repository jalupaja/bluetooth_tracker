class BLE_stats_OLD:
    # TODO code not updated
    TBL_TIME = "time"
    TBL_DEV = "ble_device"
    TBL_DEV_TIME = "ble_device_time"

    def __init__(self):
        self.db = DB(DB_PATH)
        # TODO check if loading everything is too much...
        col_names = self.db.get_columns(self.TBL_DEV)

        boring_cols = [
            "path",
            "alias",
            "paired",
            "bonded",
            "trusted",
            "blocked",
            "legacypairing",
            "rssi",
            "connected",
            "adapter",
            # "manufacturer_binary",
            "txpower",
            "servicesresolved", # TODO
            "class_name", # TODO
            "modalias", # TODO
            "geolocation",
            "AdvertisingFlags", # TODO
        ]

        arr = np.array(self.db.execute(f"SELECT * FROM {dev}"))
        df = pd.DataFrame(arr, columns = col_names)

        # remove uninteresting columns
        df = df.drop(boring_cols, axis = 1)
        # fix timestamp datatype
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        self.df = df

    def get_address(self, add):
        return self.df[self.df["address"] == add]

    def get_manufacturer(self, add):
        return self.df[self.df["manufacturers"] == add]

    def count_table(self, col):
        return self.df.groupby(col)[col].count().sort_values(ascending = False)

    def __interesting_queries():
        df = self.df

        # all columns where name != name2
        df[df['name2'].notna() & (df['name'] != df['name2'])][["name", "name2", "address", "addresstype"]]

        # get all columns where address != address2
        df[df['address2'].notna() & (df['address'] != df['address2'])][["address", "address2"]]

        # get all manufacturer_binary that could not resolve to a manufacturer
        df[(df['manufacturers'].isna() & df['manufacturer_binary'].notna())][["manufacturers", "manufacturer_binary", "address"]]

        # get all manufacturers
        df['manufacturers'].unique()

        # Group by 'address' and get the first and last timestamp for each group
        grouped = df.groupby('address')['timestamp'].agg(['first', 'last'])
        # Calculate the difference in minutes
        grouped['minutes_diff'] = (grouped['last'] - grouped['first']).dt.total_seconds() / 60
