import sqlite3
import numpy as np
import pandas as pd

db_file = "db.db"

con = sqlite3.connect(db_file)
cur = con.cursor()

# get col_names
def get_col_names(table):
    cur.execute(f"PRAGMA table_info({table})")
    columns_info = cur.fetchall()
    return [col[1] for col in columns_info]

col_names = get_col_names("ble_devices")

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

cur.execute("SELECT * FROM ble_devices")
arr = np.array(cur.fetchall())
df = pd.DataFrame(arr, columns = col_names)

# remove uninteresting columns
df = df.drop(boring_cols, axis = 1)
# fix timestamp datatype
df['timestamp'] = pd.to_datetime(df['timestamp'])

def get_address(add):
    return df[df["address"] == add]

def get_manufacturer(add):
    return df[df["manufacturers"] == add]

def count_table(col):
    return df.groupby(col)[col].count().sort_values(ascending = False)

def __interesting_queries():
    # all columns where name != name2
    df[df['name2'].notna() & (df['name'] != df['name2'])][["name", "name2", "address", "addresstype"]]

    # get all columns where address != address2
    df[df['address2'].notna() & (df['address'] != df['address2'])][["adress", "address2"]]

    # get all manufacturer_binary that could not resolve to a manufacturer
    df[(df['manufacturers'].isna() & df['manufacturer_binary'].notna())][["manufacturers", "manufacturer_binary", "address"]]

    # get all manufacturers
    df['manufacturers'].unique()

    # Group by 'address' and get the first and last timestamp for each group
    grouped = df.groupby('address')['timestamp'].agg(['first', 'last'])
    # Calculate the difference in minutes
    grouped['minutes_diff'] = (grouped['last'] - grouped['first']).dt.total_seconds() / 60
