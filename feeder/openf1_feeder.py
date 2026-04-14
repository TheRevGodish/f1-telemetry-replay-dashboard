import requests
import time
from datetime import datetime

CARDATA_OPENF1_URL = "https://api.openf1.org/v1/car_data"
API_URL = "http://localhost:8000/telemetry" # envoi FastAPI

SESSION_KEY = 11245
DRIVER_NUMBER = 10

START_FROM = datetime.fromisoformat("2026-03-15T06:58:00.000000+00:00")

session = requests.Session()

def fetch_telemetry() -> list:
    print(f"Fetching telemetry data for driver: driver:{DRIVER_NUMBER}, session:{SESSION_KEY}")
    response = requests.get(CARDATA_OPENF1_URL, params={
        'session_key': SESSION_KEY,
        'driver_number': DRIVER_NUMBER
    })
    response.raise_for_status()
    data = response.json()
    data.sort(key = lambda x: x["date"])
    print(f"{len(data)} points de télémétrie récupérés.")
    return data

def parse_points(point: dict) -> dict:
    return {
        "speed": point.get("speed", 0),
        "throttle": point.get("throttle", 0),
        "brake": point.get("brake", 0),
        "rpm": point.get("rpm", 0),
        "n_gear": point.get("n_gear", 0),
        "drs": point.get("drs", 0),
        "timestamp": point.get("date")
    }

def replay(data: list):
    start_idx = next(
        (i for i, p in enumerate(data)
         if datetime.fromisoformat(p["date"]) >= START_FROM),
        0
    )
    print(f"Startin replay from point n°{start_idx} — {data[start_idx]['date']}")

    for idx in range(start_idx, len(data)):
        point = data[idx]
        payload = parse_points(point)
        try:
            start = time.time()
            response = session.post(API_URL, json=payload)
            elapsed = time.time() - start
            print(f"Sending point n°{idx} - {response.status_code} - request took {elapsed:.3f}s")
        except requests.exceptions.RequestException as e:
            print("Error while sending data_point for replay, trying next data_point", e)

        if idx < len(data) - 1:
            t_current = datetime.fromisoformat(data[idx]["date"])
            t_next = datetime.fromisoformat(data[idx + 1]["date"])
            delta = (t_next - t_current).total_seconds()
            time.sleep(max(0.0, min(delta, 1.0)))


def main():
    data = fetch_telemetry()
    replay(data)

if __name__ == "__main__":
    main()
