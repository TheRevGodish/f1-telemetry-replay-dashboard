import argparse
import os
import time

import psycopg
import requests

CARDATA_OPENF1_URL = "https://api.openf1.org/v1/car_data"
LOCATION_OPENF1_URL = "https://api.openf1.org/v1/location"
DRIVERS_OPENF1_URL = "https://api.openf1.org/v1/drivers"

# OpenF1 limits to 3 req/s and 30 req/min
REQUEST_DELAY_S = 2.0

DB_DSN = os.environ.get(
    "DB_DSN",
    "postgresql://f1user:f1password@localhost:5432/f1data",
)

DEFAULT_SESSION_KEY = 11245  # China 2026

def fetch_endpoint(session: requests.Session, url: str, session_key: int, driver_number: int) -> list[dict]:
    name = url.rsplit("/", 1)[-1]
    print(f"Fetching {name}, session={session_key}, driver={driver_number}")
    response = session.get(
        url,
        params={"session_key": session_key, "driver_number": driver_number},
    )
    response.raise_for_status()
    data = response.json()

    # sorting by date
    data.sort(key=lambda p: p["date"])
    print(f"{len(data)} points {name} fetched.")
    return data

def fetch_drivers(session: requests.Session, session_key: int) -> list[int]:
    """Return the sorted list of driver numbers entered in a session"""
    print(f"Fetching drivers, session={session_key}")
    response = session.get(DRIVERS_OPENF1_URL, params={"session_key": session_key})
    response.raise_for_status()
    numbers = sorted({d["driver_number"] for d in response.json()})
    print(f"{len(numbers)} drivers found: {numbers}")
    return numbers

def to_car_data_row(point: dict, session_key: int, driver_number: int) -> tuple:
    return (
        session_key,
        driver_number,
        point["date"], # psycopg parses ISO 8601 to TIMESTAMPTZ
        point.get("speed"),
        point.get("throttle"),
        point.get("brake"),
        point.get("rpm"),
        point.get("n_gear"),
        point.get("drs"), # can be None -> NULL in base
    )

def to_location_row(point: dict, session_key: int, driver_number: int) -> tuple:
    return (
        session_key,
        driver_number,
        point["date"],
        point.get("x"),
        point.get("y"),
        point.get("z"),
    )

def insert_car_data(conn: psycopg.Connection, rows: list[tuple]) -> int:
    sql = """
        INSERT INTO car_data
            (session_key, driver_number, date, speed, throttle, brake, rpm, n_gear, drs)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (session_key, driver_number, date) DO NOTHING
    """
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
        inserted = cur.rowcount
    conn.commit()
    return inserted

def insert_location(conn: psycopg.Connection, rows: list[tuple]) -> int:
    sql = """
        INSERT INTO location
            (session_key, driver_number, date, x, y, z)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (session_key, driver_number, date) DO NOTHING
    """
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
        inserted = cur.rowcount
    conn.commit()
    return inserted

def is_already_ingested(conn: psycopg.Connection, session_key: int, driver_number: int) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM car_data WHERE session_key = %s AND driver_number = %s LIMIT 1",
            (session_key, driver_number),
        )
        return cur.fetchone() is not None

def ingest_driver(http: requests.Session, conn: psycopg.Connection, session_key: int, driver_number: int) -> None:
    car_data = fetch_endpoint(http, CARDATA_OPENF1_URL, session_key, driver_number)
    time.sleep(REQUEST_DELAY_S)
    location = fetch_endpoint(http, LOCATION_OPENF1_URL, session_key, driver_number)

    if car_data:
        rows = [to_car_data_row(p, session_key, driver_number) for p in car_data]
        inserted = insert_car_data(conn, rows)
        print(f"driver {driver_number} car_data: {inserted} new lines inserted (on {len(rows)} points)")
    if location:
        rows = [to_location_row(p, session_key, driver_number) for p in location]
        inserted = insert_location(conn, rows)
        print(f"driver {driver_number} location: {inserted} new lines inserted (on {len(rows)} points)")

def main() -> None:
    parser = argparse.ArgumentParser(description="Ingestion OpenF1 -> PostgreSQL")
    parser.add_argument("--session-key", type=int, default=DEFAULT_SESSION_KEY)
    parser.add_argument(
        "--driver-number",
        type=int,
        default=None,
        help="Ingest a single driver and omit to ingest every other driver in the session",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-ingest drivers even if they are already in the database",
    )
    args = parser.parse_args()

    http = requests.Session()

    if args.driver_number is not None:
        drivers = [args.driver_number]
    else:
        drivers = fetch_drivers(http, args.session_key)
        time.sleep(REQUEST_DELAY_S)

    with psycopg.connect(DB_DSN) as conn:
        for i, driver_number in enumerate(drivers, start=1):
            if not args.force and is_already_ingested(conn, args.session_key, driver_number):
                print(f"--- [{i}/{len(drivers)}] driver {driver_number} already ingested -> skipping ---")
                continue

            print(f"--- [{i}/{len(drivers)}] driver {driver_number} ---")
            ingest_driver(http, conn, args.session_key, driver_number)

            if i < len(drivers):
                time.sleep(REQUEST_DELAY_S)


if __name__ == "__main__":
    main()
