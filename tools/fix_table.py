import sqlite3
from lib.db import BluetoothDatabase, DB

DB_PATH = "db/hci.db"

columns = ["name", "name2", "address", "address2", "addresstype", "alias", "appearance", "paired", "bonded", "trusted", "blocked", "legacypairing", "connected", "uuids", "manufacturers", "manufacturer_binary", "ServiceData", "AdvertisingFlags", "advertisingdata", "txpower", "servicesresolved", "class_of_device", "modalias", "icon"]

table_name = "ble_device"

create_table = BluetoothDatabase().table_ble_device

db = DB(DB_PATH)

db.execute(f"ALTER TABLE {table_name} RENAME TO old_{table_name}")

# db.execute(f"ALTER TABLE old_{table_name} RENAME COLUMN class_name TO class_of_device")

db.execute(create_table)

insert_query = f"""
    INSERT INTO {table_name} ({', '.join(columns)})
    SELECT {', '.join(columns)} FROM old_{table_name};
"""
db.execute(insert_query)

db.execute(f"DROP TABLE old_{table_name};")

db.commit()
db.close()
