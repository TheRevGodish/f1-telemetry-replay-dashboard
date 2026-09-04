import os
import requests
import threading
import time
from datetime import datetime

import psycopg
from psycopg.rows import dict_row

TELEMETRY_URL = "http://api:8000/telemetry"
LOCATION_URL = "http://api:8000/location"

DB_DSN = os.environ.get(
    "DB_DSN",
    "postgresql://f1user:f1password@postgres:5432/f1data",
)

SESSION_KEY = 11245

# 07:00 = effective time departure
START_FROM = datetime.fromisoformat("2026-03-15T07:00:00.000000+00:00")

def fetch_driver_numbers() -> list[int]:
    sql = """
        SELECT driver_number
        FROM car_data
        WHERE session_key = %s
        GROUP BY driver_number
        HAVING MAX(speed) > 0
        ORDER BY driver_number
    """
    with psycopg.connect(DB_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (SESSION_KEY,))
            numbers = [row[0] for row in cur.fetchall()]
    print(f"Replaying {len(numbers)} drivers: {numbers}")
    return numbers

def fetch_rows(table: str, columns: str, driver_number: int) -> list:
    print(f"Reading {table} from Postgres for driver:{driver_number}, session:{SESSION_KEY}")
    sql = f"""
        SELECT date, {columns}
        FROM {table}
        WHERE session_key = %s AND driver_number = %s
        ORDER BY date
    """
    with psycopg.connect(DB_DSN) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, (SESSION_KEY, driver_number))
            rows = cur.fetchall()

    data = [{**row, "date": row["date"].isoformat()} for row in rows]
    print(f"driver {driver_number}: {len(data)} points {table} fetched.")
    return data

def fetch_telemetry(driver_number: int) -> list:
    return fetch_rows("car_data", "speed, throttle, brake, rpm, n_gear, drs", driver_number)

def fetch_location(driver_number: int) -> list:
    return fetch_rows("location", "x, y, z", driver_number)

def parse_telemetry(point: dict, driver_number: int) -> dict:
    return {
        "driver_number": driver_number,
        "speed": point.get("speed", 0),
        "throttle": point.get("throttle", 0),
        "brake": point.get("brake", 0),
        "rpm": point.get("rpm", 0),
        "n_gear": point.get("n_gear", 0),
        "drs": point.get("drs") or 0,
        "timestamp": point.get("date")
    }

def parse_location(point: dict, driver_number: int) -> dict:
    return {
        "driver_number": driver_number,
        "x": point.get("x", 0),
        "y": point.get("y", 0),
        "z": point.get("z", 0),
        "timestamp": point.get("date")
    }

def replay(data: list, driver_number: int, wall_start: float, url: str, parse_fn, label: str):
    http = requests.Session()  # one Session per thread : requests isn't thread-safe

    start_idx = next(
        (i for i, p in enumerate(data)
         if datetime.fromisoformat(p["date"]) >= START_FROM),
        0
    )
    print(f"driver:{driver_number} [{label}], starting replay from point n°{start_idx}, {data[start_idx]['date']}")

    for idx in range(start_idx, len(data)):
        point = data[idx]

        offset = (datetime.fromisoformat(point["date"]) - START_FROM).total_seconds()
        sleep_for = (wall_start + offset) - time.monotonic()
        if sleep_for > 0:
            time.sleep(sleep_for)

        try:
            response = http.post(url, json=parse_fn(point, driver_number))
            if response.status_code != 200:
                print(f"driver:{driver_number} [{label}],point n°{idx} rejected: {response.status_code} {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"driver:{driver_number} [{label}], error sending point n°{idx}, trying next one", e)

    print(f"driver:{driver_number} [{label}],replay finished.")

def main():
    driver_numbers = fetch_driver_numbers()
    jobs = []
    for d in driver_numbers:
        jobs.append((fetch_telemetry(d), d, TELEMETRY_URL, parse_telemetry, "car_data"))
        jobs.append((fetch_location(d), d, LOCATION_URL, parse_location, "location"))

    wall_start = time.monotonic()
    threads = [
        threading.Thread(
            target=replay,
            args=(data, d, wall_start, url, parse_fn, label),
            name=f"{label}-{d}",
        )
        for data, d, url, parse_fn, label in jobs
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
