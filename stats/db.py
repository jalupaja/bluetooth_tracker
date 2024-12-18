import sqlite3

class DB:
    def __init__(self, path):
        self.path = path
        self.con = sqlite3.connect(path)
        self.cur = self.con.cursor()

    def __del__(self):
        self.con.close()

    def get_tables(self):
        tables = self.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [t[0] for t in tables]

    def get_columns(self, table):
        columns_info = self.execute(f"PRAGMA table_info({table})")
        return [col[1] for col in columns_info]

    def execute(self, query):
        self.cur.execute(query)
        return self.cur.fetchall()

    def close(self):
        self.__del__()

