import sqlite3

DB_PATH = "TEST.db"

columns = ["name", "name2", "address", "address2", "addresstype", "alias", "appearance", "paired", "bonded", "trusted", "blocked", "legacypairing", "connected", "uuids", "manufacturers", "manufacturer_binary", "ServiceData", "AdvertisingFlags", "txpower", "servicesresolved", "class_name", "modalias", "icon"]

table_name = "ble_device"

create_table = """CREATE TABLE IF NOT EXISTS ble_device (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  name2 TEXT,
                  address TEXT,
                  address2 TEXT,
                  addresstype TEXT,
                  alias TEXT,
                  appearance TEXT,
                  paired BOOLEAN,
                  bonded BOOLEAN,
                  trusted BOOLEAN,
                  blocked BOOLEAN,
                  legacypairing BOOLEAN,
                  connected BOOLEAN,
                  uuids TEXT,
                  manufacturers TEXT,
                  manufacturer_binary BLOB,
                  ServiceData TEXT,
                  AdvertisingFlags BLOB,
                  txpower INTEGER,
                  servicesresolved BOOLEAN,
                  class_name TEXT,
                  modalias TEXT,
                  icon TEXT
                  ) """

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute(f"ALTER TABLE {table_name} RENAME TO old_{table_name}")

cursor.execute(create_table)

insert_query = f"""
    INSERT INTO {table_name} ({', '.join(columns)})
    SELECT {', '.join(columns)} FROM old_{table_name};
"""
cursor.execute(insert_query)

cursor.execute(f"DROP TABLE old_{table_name};")

conn.commit()
conn.close()
