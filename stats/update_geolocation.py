from datetime import datetime
from db import DB

def update_geolocation(db, date, start_time, end_time, new_geolocation):
    start_time = f"{date} {start_time}"
    end_time = f"{date} {end_time}"

    try:
        datetime.strptime(start_time, "%Y-%m-%d %H:%M")
        datetime.strptime(end_time, "%Y-%m-%d %H:%M")
    except ValueError:
        print("Invalid date or time format. Use 'YYYY-MM-DD' for date and 'HH:MM' for time.")
        return

    db.cur.execute("""
        UPDATE time
        SET geolocation = ?
        WHERE timestamp >= ? AND timestamp <= ?;
    """, (new_geolocation, start_time, end_time))
    db.commit()

    db.cur.execute("""
        SELECT * FROM time
        WHERE timestamp >= ? AND timestamp <= ?;
    """, (start_time, end_time))
    rows = db.cur.fetchall()
    print(f"{len(rows)} rows affected")

db = DB("../db/db.db")
while True:
    day = input("Day: ")
    if day == "":
        break

    while True:
        start = input("start time: ")
        if start == "":
            break

        end = input("end time:   ")
        if end == "":
            break

        place = input("place:      ")
        if place == "":
            break
        update_geolocation(db, f"2024-12-{day}", start, end, place)

db.close()
