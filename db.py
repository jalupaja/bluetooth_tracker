import sqlite3

class DB:
    def __init__(self, db_name='db.db'):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                name2 TEXT,
                address TEXT,
                address2 TEXT,
                path TEXT,
                addresstype TEXT,
                alias TEXT,
                paired BOOLEAN,
                bonded BOOLEAN,
                trusted BOOLEAN,
                blocked BOOLEAN,
                legacypairing BOOLEAN,
                rssi INTEGER,
                connected BOOLEAN,
                uuids TEXT,
                adapter TEXT,
                manufacturers TEXT,
                manufacturer_binary BLOB,
                txpower INTEGER,
                servicesresolved BOOLEAN,
                class_name TEXT,
                modalias TEXT,
                icon TEXT
            )
        ''')
        self.connection.commit()

    def insert_device(self, device):
        self.cursor.execute('''
            INSERT INTO devices (
                name, name2, address, address2, addresstype, alias,
                paired, bonded, trusted, blocked, legacypairing, rssi,
                connected, uuids, manufacturers, manufacturer_binary,
                txpower, servicesresolved, class_name, modalias, icon
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            device.name,
            device.name2,
            device.address,
            device.address2,
            device.addresstype,
            device.alias,
            device.paired,
            device.bonded,
            device.trusted,
            device.blocked,
            device.legacypairing,
            device.rssi,
            device.connected,
            device.uuids,
            device.manufacturers,
            device.manufacturer_binary,
            device.txpower,
            device.servicesresolved,
            device.class_name,
            device.modalias,
            device.icon
        ))
        self.connection.commit()

    def close(self):
        # Close the database connection
        self.connection.close()

