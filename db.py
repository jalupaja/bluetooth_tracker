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
                icon TEXT,
                props TEXT
            )
        ''')
        self.connection.commit()

    def insert_device(self, device):
        # Insert device information into the table
        self.cursor.execute('''
            INSERT INTO devices (
                name, name2, path, address, address2, addresstype, alias,
                paired, bonded, trusted, blocked, legacypairing, rssi,
                connected, uuids, adapter, manufacturers, manufacturer_binary,
                txpower, servicesresolved, class_name, modalias, icon, props
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            device.name,
            device.name2,
            device.path,
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
            device.adapter,
            device.manufacturers,
            device.manufacturer_binary,
            device.txpower,
            device.servicesresolved,
            device.class_name,
            device.modalias,
            device.icon,
            device.props
        ))
        self.connection.commit()

    def close(self):
        # Close the database connection
        self.connection.close()

# TODO
# Example usage:
if __name__ == "__main__":
    db = DB()

    # Example device info dictionary
    device_info = {
        'name': 'Device1',
        'name2': 'Device2',
        'path': '/path/to/device',
        'address': '00:11:22:33:44:55',
        'address2': '66:77:88:99:AA:BB',
        'addresstype': 'type1',
        'alias': 'MyDevice',
        'paired': True,
        'bonded': True,
        'trusted': True,
        'blocked': False,
        'legacypairing': False,
        'rssi': -60,
        'connected': True,
        'uuids': 'uuid1, uuid2',
        'adapter': 'Adapter1',
        'manufacturers': 'Manufacturer1',
        'manufacturer_binary': b'\x01\x02',
        'txpower': 5,
        'servicesresolved': True,
        'class_name': 'Class1',
        'modalias': 'modalias1',
        'icon': 'icon.png',
        'props': 'Some props'
    }

    db.insert_device(device_info)
    db.close()
