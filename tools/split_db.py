import sqlite3

source_db = "db/db.BAK"
target_db = "/tmp/test.db"

lower_date = "2024-12-28"
upper_date = "2024-12-31"

source_conn = sqlite3.connect(source_db)
target_conn = sqlite3.connect(target_db)

source_cursor = source_conn.cursor()
target_cursor = target_conn.cursor()

tables = [
    """CREATE TABLE IF NOT EXISTS time (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP,
        geolocation TEXT
    );""",
    """CREATE TABLE IF NOT EXISTS bluetooth_device_time (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER,
        time_id INTEGER,
        FOREIGN KEY (device_id) REFERENCES bluetooth_device (id),
        FOREIGN KEY (time_id) REFERENCES time (id)
    );""",
    """CREATE TABLE IF NOT EXISTS ble_device_time (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER,
        time_id INTEGER,
        FOREIGN KEY (device_id) REFERENCES ble_device (id),
        FOREIGN KEY (time_id) REFERENCES time (id)
    );""",
    """CREATE TABLE IF NOT EXISTS bluetooth_device (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        address TEXT,
        name TEXT,
        device_class TEXT,
        manufacturer TEXT,
        version TEXT,
        hci_version TEXT,
        lmp_version TEXT,
        device_type TEXT,
        device_id TEXT,
        extra_hci_info TEXT,
        services TEXT
    );""",
    """CREATE TABLE IF NOT EXISTS ble_device (
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
    );""",
    """CREATE TABLE IF NOT EXISTS bluetooth_service (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        host TEXT,
        name TEXT,
        service_classes TEXT,
        profiles TEXT,
        description TEXT,
        provider TEXT,
        service_id TEXT,
        protocol TEXT,
        port INTEGER
    );""",
    """CREATE TABLE IF NOT EXISTS bluetooth_device_service (
        device_id INTEGER,
        service_id INTEGER,
        time_id INTEGER,
        FOREIGN KEY (device_id) REFERENCES bluetooth_device (id),
        FOREIGN KEY (service_id) REFERENCES bluetooth_service (id),
        FOREIGN KEY (time_id) REFERENCES time (id)
    );"""
]

for table in tables:
    target_cursor.execute(table)

source_cursor.execute("""
    SELECT * FROM time WHERE Date(timestamp) >= ? AND Date(timestamp) <= ?;
""", (lower_date, upper_date))
time_rows = source_cursor.fetchall()
time_ids = [row[0] for row in time_rows]

for row in time_rows:
    target_cursor.execute("""
        INSERT INTO time (id, timestamp, geolocation) VALUES (?, ?, ?);
    """, row)

related_time_tables = [("ble_device_time", "device_id", "time_id"),
                       ("bluetooth_device_time", "device_id", "time_id")]

device_ids = set()
for table, device_column, time_column in related_time_tables:
    source_cursor.execute(f"""
        SELECT * FROM {table} WHERE {time_column} IN ({','.join('?' * len(time_ids))});
    """, time_ids)
    rows = source_cursor.fetchall()

    for row in rows:
        target_cursor.execute(f"""
            INSERT INTO {table} VALUES ({','.join(['?'] * len(row))});
        """, row)
        device_ids.add(row[1])

device_tables = [("bluetooth_device", "id"), ("ble_device", "id")]

for table, column in device_tables:
    source_cursor.execute(f"""
        SELECT * FROM {table} WHERE {column} IN ({','.join('?' * len(device_ids))});
    """, list(device_ids))
    rows = source_cursor.fetchall()
    for row in rows:
        target_cursor.execute(f"""
            INSERT INTO {table} VALUES ({','.join(['?'] * len(row))});
        """, row)

source_cursor.execute(f"""
    SELECT * FROM bluetooth_device_service WHERE time_id IN ({','.join('?' * len(time_ids))});
""", time_ids)
bluetooth_device_service_rows = source_cursor.fetchall()
service_ids = set()

for row in bluetooth_device_service_rows:
    target_cursor.execute("""
        INSERT INTO bluetooth_device_service (device_id, service_id, time_id) VALUES (?, ?, ?);
    """, row)
    service_ids.add(row[1])

source_cursor.execute(f"""
    SELECT * FROM bluetooth_service WHERE id IN ({','.join('?' * len(service_ids))});
""", list(service_ids))
bluetooth_service_rows = source_cursor.fetchall()

for row in bluetooth_service_rows:
    target_cursor.execute("""
        INSERT INTO bluetooth_service (id, host, name, service_classes, profiles, description, provider, service_id, protocol, port)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, row)

target_conn.commit()

